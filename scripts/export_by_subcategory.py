"""
Utility script to export articles by subcategory for Dify knowledge base.

This script helps organize exported articles into subcategory-specific directories,
making it easier to create separate knowledge bases for different topics.
"""
import os
import sys
import argparse
from loguru import logger

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import DatabaseManager
from config.category_taxonomy import CATEGORY_TAXONOMY, get_category_path


def export_by_subcategory(
    output_base_dir: str,
    category: str = None,
    min_quality: float = 0.5
):
    """
    Export articles organized by subcategory.

    Args:
        output_base_dir: Base output directory
        category: Top-level category filter (optional)
        min_quality: Minimum quality score
    """
    db = DatabaseManager()

    categories_to_export = [category] if category else CATEGORY_TAXONOMY.keys()

    for cat_key in categories_to_export:
        logger.info(f"\nExporting category: {cat_key}")

        cat_data = CATEGORY_TAXONOMY[cat_key]
        cat_name = cat_data["name"]

        for sub_key, sub_data in cat_data["subcategories"].items():
            logger.info(f"  Subcategory: {sub_key} - {sub_data['name']}")

            # Create directory structure: base/一级分类/二级分类/
            sub_dir = os.path.join(output_base_dir, f"{cat_key}_{cat_name}", f"{sub_key}_{sub_data['name']}")
            os.makedirs(sub_dir, exist_ok=True)

            # Export articles for this subcategory
            db.export_articles_to_txt(
                output_dir=sub_dir,
                source=None,
                category=cat_key,
                min_quality=min_quality
            )

            # Now create sub-subcategory directories
            for sub_sub_key, sub_sub_data in sub_data["sub_subcategories"].items():
                logger.info(f"    Sub-subcategory: {sub_sub_key} - {sub_sub_data['name']}")

                # Create directory: base/一级分类/二级分类/三级分类/
                sub_sub_dir = os.path.join(sub_dir, f"{sub_sub_key}_{sub_sub_data['name']}")
                os.makedirs(sub_sub_dir, exist_ok=True)

                # Export articles for this sub-subcategory
                db.export_articles_to_txt(
                    output_dir=sub_sub_dir,
                    source=None,
                    category=cat_key,
                    min_quality=min_quality
                )

    logger.info(f"\nExport completed! Base directory: {output_base_dir}")
    logger.info("\nDirectory structure:")
    _print_directory_structure(output_base_dir)


def _print_directory_structure(directory: str, indent: int = 0):
    """Print directory structure."""
    try:
        entries = sorted(os.listdir(directory))
        for entry in entries:
            path = os.path.join(directory, entry)
            if os.path.isdir(path):
                print("  " * indent + f"📁 {entry}/")
                _print_directory_structure(path, indent + 1)
            else:
                print("  " * indent + f"📄 {entry}")
    except Exception as e:
        logger.error(f"Error listing directory: {e}")


def export_flat_by_sub_subcategory(output_dir: str, min_quality: float = 0.5):
    """
    Export articles with flat structure, one directory per sub-subcategory.

    This is useful for Dify when you want separate knowledge bases for each
    specific topic.

    Directory structure:
    output_dir/
    ├── 抑郁障碍/
    ├── 焦虑障碍/
    ├── 人力资源规划/
    ├── 薪酬绩效/
    ├── 增值税/
    └── ...

    Args:
        output_dir: Output directory
        min_quality: Minimum quality score
    """
    db = DatabaseManager()

    for cat_key, cat_data in CATEGORY_TAXONOMY.items():
        for sub_key, sub_data in cat_data["subcategories"].items():
            for sub_sub_key, sub_sub_data in sub_data["sub_subcategories"].items():
                # Create directory for this sub-subcategory
                dir_name = f"{sub_sub_data['name']}"
                sub_dir = os.path.join(output_dir, dir_name)
                os.makedirs(sub_dir, exist_ok=True)

                # Export articles
                db.export_articles_to_txt(
                    output_dir=sub_dir,
                    source=None,
                    category=cat_key,
                    min_quality=min_quality
                )

                logger.info(f"Exported: {dir_name}")

    logger.info(f"\nExport completed! Directory: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Export articles by subcategory for Dify knowledge base"
    )

    parser.add_argument("--output", "-o", required=True, help="Output base directory")
    parser.add_argument("--category", "-c", help="Filter by top-level category")
    parser.add_argument("--min-quality", "-q", type=float, default=0.5,
                       help="Minimum quality score (default: 0.5)")
    parser.add_argument("--flat", "-f", action="store_true",
                       help="Use flat structure (one directory per sub-subcategory)")

    args = parser.parse_args()

    try:
        if args.flat:
            export_flat_by_sub_subcategory(args.output, args.min_quality)
        else:
            export_by_subcategory(args.output, args.category, args.min_quality)

    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
