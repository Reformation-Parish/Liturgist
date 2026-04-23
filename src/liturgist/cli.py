"""
Command-line interface for liturgist.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import pypandoc
import typst
from weasyprint import HTML

from .core import (
    load_template_from_file,
    next_sunday,
    process_schedule_data,
    read_schedule,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="A liturgical document generator")
    parser.add_argument(
        "--date",
        help="A date on the schedule to select data for the template. "
        + "Defaults to next sunday if unspecified.",
    )
    parser.add_argument(
        "--print-json",
        dest="print_json",
        help="Print selected data as JSON.",
        action="store_true",
    )
    parser.add_argument(
        "--bible-json-path",
        dest="bible_json_path",
        help="A file containing the verses in json arrays",
    )
    parser.add_argument("--template", help="A path to a mustache template")
    parser.add_argument(
        "-o",
        "--output",
        dest="output_path",
        help="A path to the output file",
        default="output/out.pdf",
    )
    parser.add_argument(
        "schedule", help="A path to a schedule - csv, ods, xlsx, and json are supported"
    )

    return parser.parse_args()


def render_output(
    rendered_content: str,
    output_path: str,
    template_path: Optional[Path],
) -> None:
    """
    Render content to the specified output format.

    Args:
        rendered_content: The rendered template content
        output_path: Path to save the output file
        template_path: Path to the original template (for format detection)
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    file_extension = output_path_obj.suffix.lower()

    try:
        if template_path.suffix.lower() == ".html":
            if file_extension == ".pdf":
                HTML(string=rendered_content).write_pdf(output_path)
            elif file_extension in [".docx", ".odt"]:
                if template_path:
                    template_file_extension = template_path.suffix.lstrip(".")
                else:
                    # Default to HTML if no template path provided
                    template_file_extension = "html"

                pypandoc.convert_text(
                    rendered_content,
                    format=template_file_extension,
                    to=file_extension.lstrip("."),
                    outputfile=output_path,
                )
            else:
                # Plain text output
                output_path_obj.write_text(rendered_content, encoding="utf-8")

            print(f"{output_path} generated successfully", file=sys.stderr)
        elif template_path.suffix.lower() == ".typ" and file_extension == ".pdf":
            typst.compile(rendered_content.encode("utf-8"), output_path)
            print(f"{output_path} generated successfully", file=sys.stderr)
        else:
            print(
                f"Unable to generate {output_path} from {template_path}",
                file=sys.stderr,
            )

    except Exception as e:
        print(f"Error generating output: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    args = parse_arguments()

    # Parse date
    if args.date is not None:
        try:
            date = pd.to_datetime(args.date).date()
        except Exception as e:
            print(f"Error parsing date '{args.date}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        date = next_sunday()

    # Validate arguments
    if args.template is None and not args.print_json:
        print("You must specify a template file or --print-json.", file=sys.stderr)
        sys.exit(1)

    # Read schedule
    try:
        schedule = read_schedule(args.schedule)
    except Exception as e:
        print(f"Error reading schedule: {e}", file=sys.stderr)
        sys.exit(1)

    # Process schedule data
    try:
        data = process_schedule_data(schedule, date, args.bible_json_path)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing schedule data: {e}", file=sys.stderr)
        sys.exit(1)

    # Output JSON if requested
    if args.print_json:
        print(json.dumps(data, indent=2))

    # Render template if provided
    if args.template is not None:
        template_path = Path(args.template)
        if not template_path.is_file():
            print(f"Unable to open template file: {template_path}", file=sys.stderr)
            sys.exit(1)

        try:
            template = load_template_from_file(template_path)
            rendered_content = template(data)
            render_output(rendered_content, args.output_path, template_path)
        except Exception as e:
            print(f"Error rendering template: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
