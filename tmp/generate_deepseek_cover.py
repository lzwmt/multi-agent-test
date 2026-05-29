from openai import OpenAI
import base64
from pathlib import Path

api_key = 'sk-XvsVyVM57ZHeR0t0rHax3sGee5GPRiwNquVDMNj4ZPagySfN'
client = OpenAI(api_key=api_key, base_url='https://api-xai.ainaibahub.com/v1')
prompt = '''16:9 horizontal cover image for a technology commentary article. Theme: DeepSeek V4 is "building roads" rather than "setting off fireworks". Deep navy and black high-tech background. A futuristic highway made of circuit traces, data streams, optical light paths, and token-grid tiles extends toward the horizon in strong perspective. At the far end, an abstract silhouette of large-model infrastructure: modular data centers, neural network cores, server racks, cooling towers, fiber backbones, all stylized and non-literal. Industrial, infrastructure-focused, efficient, calm, serious, restrained. Subtle blue/cyan glow accents, metallic surfaces, clean composition with negative space for headline. No people, no real text, no readable characters, no logos, no watermark, not flashy, not fireworks, suitable for a WeChat public account long-form tech article cover. Cinematic, sharp, premium editorial illustration, 16:9 aspect ratio.'''
result = client.images.generate(model='gpt-image-2', prompt=prompt, size='1792x1024')
b64 = result.data[0].b64_json
out = Path('tmp/deepseek_v4_cover_generated.png')
out.write_bytes(base64.b64decode(b64))
print(out)
