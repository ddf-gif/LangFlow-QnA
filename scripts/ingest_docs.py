"""
文档导入脚本 — 将知识文档导入向量库

用法:
    python scripts/ingest_docs.py                          # 使用默认目录 data/knowledge/
    python scripts/ingest_docs.py --dir ./my_docs          # 指定目录
"""
import argparse
from pathlib import Path

# scripts/ 目录不在 Python 包路径中
# 需要手动添加项目根目录
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.pipeline import ingest_directory


def main():
    parser = argparse.ArgumentParser(description="导入知识文档到向量库")
    parser.add_argument(
        "--dir",
        type=str,
        default="data/knowledge",
        help="文档目录路径（默认: data/knowledge/）",
    )
    args = parser.parse_args()

    docs_dir = Path(args.dir)
    if not docs_dir.is_absolute():
        # 相对于项目根目录
        docs_dir = Path(__file__).resolve().parent.parent / docs_dir

    print(f"📂 文档目录: {docs_dir}")
    ingest_directory(docs_dir)


if __name__ == "__main__":
    main()
