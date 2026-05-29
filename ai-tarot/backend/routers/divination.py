"""
Divination router - handles tarot reading requests.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Divination, User
from ..services.tarot import TarotEngine
from ..services.ai_reader import AIReader
from ..services.content_safe import ContentSafety

router = APIRouter(prefix="/api/divination", tags=["divination"])

# Singletons
_engine = TarotEngine()
_engine.load_cards()
_engine.load_spreads()
_reader = AIReader()
_safety = ContentSafety()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class DivinationRequest(BaseModel):
    spread_type: str = "three_card"
    question: str = ""
    persona: str = "gentle_sister"


class CardInfo(BaseModel):
    id: int
    name_cn: str
    name_en: str
    orientation: str
    position_name: str
    upright_keywords: list[str]
    reversed_keywords: list[str]
    drawn_id: int
    suit: str | None = None
    number: int | None = None


class DivinationResponse(BaseModel):
    id: int
    spread_type: str
    spread_name: str
    cards: list[CardInfo]
    question: str
    answer: str
    persona: str


class SpreadInfo(BaseModel):
    id: str
    name_cn: str
    name_en: str
    description: str
    card_count: int
    use: str = ""
    steps: list[str] = []
    tips: list[str] = []
    note: str = ""
    answer_logic: str = ""
    layout: str = ""
    position_details: list[dict] = []


class PersonaInfo(BaseModel):
    id: str
    name: str
    description: str
    style_keywords: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/spreads", response_model=list[SpreadInfo])
async def list_spreads():
    """List available tarot spreads."""
    result = []
    for key, spread in _engine._spreads.items():
        result.append(SpreadInfo(
            id=spread["id"],
            name_cn=spread["name_cn"],
            name_en=spread["name_en"],
            description=spread.get("description", ""),
            card_count=spread["card_count"],
            use=spread.get("use", ""),
            steps=spread.get("steps", []),
            tips=spread.get("tips", []),
            note=spread.get("note", ""),
            answer_logic=spread.get("answer_logic", ""),
            layout=spread.get("layout", ""),
            position_details=spread.get("position_details", []),
        ))
    return result


@router.get("/personas", response_model=list[PersonaInfo])
async def list_personas():
    """List available reader personas."""
    return _reader.list_personas()


@router.post("/", response_model=DivinationResponse)
async def create_divination(
    req: DivinationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Perform a tarot divination: draw cards, get AI reading, save to DB."""
    # 1. Content safety check on user question
    if req.question:
        safety = _safety.check_input(req.question)
        if not safety.is_safe:
            raise HTTPException(
                status_code=400,
                detail=f"检测到敏感内容，无法进行占卜。{safety.reason}"
            )

    # 2. Validate spread type
    try:
        _engine.get_spread(req.spread_type)
    except (KeyError, RuntimeError):
        raise HTTPException(
            status_code=400,
            detail=f"未知牌阵: {req.spread_type}，请使用 /api/divination/spreads 查看可用牌阵。"
        )

    # 3. Draw cards and do reading
    try:
        reading = _engine.do_reading(req.spread_type, allow_reversed=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抽牌失败: {str(e)}")

    # 4. Get AI interpretation
    try:
        if req.spread_type == "single":
            card = reading["cards"][0]
            answer = await _reader.read_card(
                persona_name=req.persona,
                card=card,
                position=card["position_name"],
                user_question=req.question or "请给我今天的指引",
            )
        else:
            answer = await _reader.full_reading(
                persona_name=req.persona,
                spread_result=reading,
                user_question=req.question or "请为我解读这个牌阵",
            )
    except Exception as e:
        # Fallback: return cards without AI reading
        answer = f"牌面已为您展开，但解牌师暂时无法连接。请稍后再来。({str(e)[:50]})"

    # 5. Content safety check on AI output
    output_safety = _safety.check_output(answer)
    if not output_safety.is_safe:
        answer = "牌面已为您展开。当前解读内容需要调整，请换个问题再试一次。"

    # 6. Save to database
    cards_data = []
    for c in reading["cards"]:
        cards_data.append({
            "name_cn": c["name_cn"],
            "name_en": c["name_en"],
            "orientation": c["orientation"],
            "position_name": c["position_name"],
            "drawn_id": c["drawn_id"],
            "upright_keywords": c.get("upright_keywords", []),
            "reversed_keywords": c.get("reversed_keywords", []),
        })

    divination = Divination(
        user_id=1,  # TODO: get from auth
        spread_type=req.spread_type,
        cards_json=cards_data,
        question=req.question or "",
        answer=answer,
        persona=req.persona,
    )
    db.add(divination)
    await db.flush()

    # 7. Build response
    card_infos = []
    for c in reading["cards"]:
        card_infos.append(CardInfo(
            id=c["id"],
            name_cn=c["name_cn"],
            name_en=c["name_en"],
            orientation=c["orientation"],
            position_name=c["position_name"],
            upright_keywords=c.get("upright_keywords", []),
            reversed_keywords=c.get("reversed_keywords", []),
            drawn_id=c["drawn_id"],
            suit=c.get("suit"),
            number=c.get("number"),
        ))

    return DivinationResponse(
        id=divination.id,
        spread_type=req.spread_type,
        spread_name=reading["spread"]["name_cn"],
        cards=card_infos,
        question=req.question or "",
        answer=answer,
        persona=req.persona,
    )


@router.get("/cross/{card_a}/{card_b}")
async def get_cross_reading(card_a: str, card_b: str):
    """Query cross interpretation for two Major Arcana cards (by number 0-21)."""
    matrix = _reader._kb_cross_matrix
    entry = matrix.get(card_a, {}).get(card_b, {})
    if not entry:
        entry = matrix.get(card_b, {}).get(card_a, {})
    return entry or {"error": "未找到交叉解读"}


@router.get("/reversed-detail/{card_id}")
async def get_reversed_detail(card_id: str):
    """Get 4-layer reverse analysis for a Major Arcana card (by number or name)."""
    detail = _reader._kb_reversed_detail.get(card_id, {})
    return detail or {"error": "未找到逆位详情"}


@router.get("/symbolism/{card_id}")
async def get_symbolism(card_id: str):
    """Get deep symbol meanings for a Major Arcana card (by number or name)."""
    sym_by_name = _reader._kb_symbolism.get("_by_name", {})
    return sym_by_name.get(card_id, {"error": "未找到符号象征"})


@router.get("/history")
async def get_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get divination history for current user."""
    stmt = (
        select(Divination)
        .where(Divination.user_id == 1)  # TODO: get from auth
        .order_by(desc(Divination.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    total_stmt = select(Divination).where(Divination.user_id == 1)
    total_result = await db.execute(total_stmt)
    total = len(total_result.scalars().all())

    return {
        "items": [
            {
                "id": d.id,
                "spread_type": d.spread_type,
                "question": d.question,
                "answer": d.answer[:100] + "..." if len(d.answer) > 100 else d.answer,
                "persona": d.persona,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in items
        ],
        "total": total,
    }


@router.get("/{divination_id}")
async def get_divination(
    divination_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific divination record."""
    stmt = select(Divination).where(Divination.id == divination_id)
    result = await db.execute(stmt)
    d = result.scalar_one_or_none()

    if not d:
        raise HTTPException(status_code=404, detail="占卜记录不存在")

    return {
        "id": d.id,
        "spread_type": d.spread_type,
        "cards": d.cards_json,
        "question": d.question,
        "answer": d.answer,
        "persona": d.persona,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }
