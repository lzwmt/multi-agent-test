#!/bin/bash

# =============================================================================
# 备份脚本 - backup.sh
# 功能：备份指定目录到 /tmp/backup，保留最近7天备份
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# 配置变量
# -----------------------------------------------------------------------------
BACKUP_DIR="/tmp/backup"
RETENTION_DAYS=7
LOG_FILE="${BACKUP_DIR}/backup.log"

# -----------------------------------------------------------------------------
# 颜色定义（用于终端输出）
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# 日志函数
# -----------------------------------------------------------------------------
log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 写入日志文件
    echo "[${timestamp}] [${level}] ${message}" >> "${LOG_FILE}"
    
    # 终端输出（带颜色）
    case "${level}" in
        INFO)
            echo -e "${GREEN}[INFO]${NC} ${message}"
            ;;
        WARN)
            echo -e "${YELLOW}[WARN]${NC} ${message}"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} ${message}"
            ;;
    esac
}

# -----------------------------------------------------------------------------
# 错误处理函数
# -----------------------------------------------------------------------------
cleanup_on_error() {
    local exit_code=$?
    log "ERROR" "脚本执行失败，退出码: ${exit_code}"
    exit "${exit_code}"
}

trap cleanup_on_error ERR

# -----------------------------------------------------------------------------
# 检查依赖
# -----------------------------------------------------------------------------
check_dependencies() {
    local deps=("tar" "date" "find" "mkdir")
    for dep in "${deps[@]}"; do
        if ! command -v "${dep}" &> /dev/null; then
            log "ERROR" "缺少必要依赖: ${dep}"
            exit 1
        fi
    done
    log "INFO" "依赖检查通过"
}

# -----------------------------------------------------------------------------
# 初始化备份目录
# -----------------------------------------------------------------------------
init_backup_dir() {
    if [[ ! -d "${BACKUP_DIR}" ]]; then
        mkdir -p "${BACKUP_DIR}" || {
            log "ERROR" "无法创建备份目录: ${BACKUP_DIR}"
            exit 1
        }
        log "INFO" "创建备份目录: ${BACKUP_DIR}"
    fi
}

# -----------------------------------------------------------------------------
# 验证源目录
# -----------------------------------------------------------------------------
validate_source() {
    local source_dir="$1"
    
    if [[ -z "${source_dir}" ]]; then
        log "ERROR" "未指定源目录"
        echo "用法: $0 <源目录路径>"
        exit 1
    fi
    
    if [[ ! -d "${source_dir}" ]]; then
        log "ERROR" "源目录不存在: ${source_dir}"
        exit 1
    fi
    
    if [[ ! -r "${source_dir}" ]]; then
        log "ERROR" "没有读取源目录的权限: ${source_dir}"
        exit 1
    fi
    
    log "INFO" "源目录验证通过: ${source_dir}"
}

# -----------------------------------------------------------------------------
# 执行备份
# -----------------------------------------------------------------------------
do_backup() {
    local source_dir="$1"
    local source_name
    source_name=$(basename "${source_dir}")
    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_filename="${source_name}_${timestamp}.tar.gz"
    local backup_path="${BACKUP_DIR}/${backup_filename}"
    
    log "INFO" "开始备份: ${source_dir}"
    log "INFO" "备份文件: ${backup_filename}"
    
    # 创建压缩备份
    if tar -czf "${backup_path}" -C "$(dirname "${source_dir}")" "${source_name}" 2>/dev/null; then
        local backup_size
        backup_size=$(du -h "${backup_path}" | cut -f1)
        log "INFO" "备份完成: ${backup_path} (${backup_size})"
    else
        log "ERROR" "备份失败: ${source_dir}"
        # 清理失败的备份文件
        [[ -f "${backup_path}" ]] && rm -f "${backup_path}"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# 清理旧备份
# -----------------------------------------------------------------------------
cleanup_old_backups() {
    local source_name="$1"
    local count_before count_after
    
    count_before=$(find "${BACKUP_DIR}" -name "${source_name}_*.tar.gz" -type f 2>/dev/null | wc -l)
    
    # 删除超过保留天数的备份
    find "${BACKUP_DIR}" -name "${source_name}_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    
    count_after=$(find "${BACKUP_DIR}" -name "${source_name}_*.tar.gz" -type f 2>/dev/null | wc -l)
    local deleted=$((count_before - count_after))
    
    if [[ ${deleted} -gt 0 ]]; then
        log "INFO" "清理完成: 删除了 ${deleted} 个旧备份文件（保留最近 ${RETENTION_DAYS} 天）"
    else
        log "INFO" "无需清理旧备份"
    fi
}

# -----------------------------------------------------------------------------
# 显示备份摘要
# -----------------------------------------------------------------------------
show_summary() {
    local source_name="$1"
    log "INFO" "========================================"
    log "INFO" "备份任务完成"
    log "INFO" "========================================"
    log "INFO" "备份目录: ${BACKUP_DIR}"
    log "INFO" "现有备份文件:"
    
    local backups
    backups=$(find "${BACKUP_DIR}" -name "${source_name}_*.tar.gz" -type f 2>/dev/null | sort -r)
    
    if [[ -n "${backups}" ]]; then
        echo "${backups}" | while read -r file; do
            local size date_str
            size=$(du -h "${file}" 2>/dev/null | cut -f1)
            date_str=$(stat -c %y "${file}" 2>/dev/null | cut -d' ' -f1)
            log "INFO" "  - $(basename "${file}") (${size}, ${date_str})"
        done
    else
        log "INFO" "  (无备份文件)"
    fi
    log "INFO" "日志文件: ${LOG_FILE}"
}

# -----------------------------------------------------------------------------
# 主函数
# -----------------------------------------------------------------------------
main() {
    local source_dir="${1:-}"
    
    echo "========================================"
    echo "       目录备份工具 v1.0"
    echo "========================================"
    
    # 检查依赖
    check_dependencies
    
    # 初始化备份目录
    init_backup_dir
    
    # 验证源目录
    validate_source "${source_dir}"
    
    local source_name
    source_name=$(basename "${source_dir}")
    
    # 执行备份
    do_backup "${source_dir}"
    
    # 清理旧备份
    cleanup_old_backups "${source_name}"
    
    # 显示摘要
    show_summary "${source_name}"
    
    log "INFO" "备份任务全部完成"
    return 0
}

# -----------------------------------------------------------------------------
# 脚本入口
# -----------------------------------------------------------------------------
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
