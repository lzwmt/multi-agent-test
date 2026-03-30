#!/bin/bash
# 示例脚本 - 用于测试代码审查流程

set -e

# 获取参数
NAME=${1:-"world"}
COUNT=${2:-5}

echo "Hello, $NAME!"
echo "Counting to $COUNT..."

# 循环
for i in $(seq 1 $COUNT); do
    echo "  $i"
done

# 检查文件
if [ -f "/tmp/test.txt" ]; then
    echo "File exists"
    cat /tmp/test.txt
else
    echo "File not found, creating..."
    echo "test content" > /tmp/test.txt
fi

echo "Done!"
