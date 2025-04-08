#!/usr/bin/env python3
"""
LaTeX to SVG Converter for EPUB2/Kindle - With Manifest Update
---------------------------------------
"""

import argparse
import glob
import os
import re
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from tqdm import tqdm

# Set LaTeX path
os.environ["PATH"] = f"{os.path.expanduser('~/bin')}:{os.environ.get('PATH', '')}"

# Configure matplotlib for LaTeX rendering
matplotlib.rcParams.update(
    {
        "font.size": 14,
        "text.usetex": True,
        "text.latex.preamble": r"\usepackage{amsmath,amssymb,bm}",
        "mathtext.fontset": "stix",
    }
)

# Register XML namespaces for EPUB OPF files
NS = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def check_latex_installation():
    """Check if LaTeX is properly installed and accessible"""
    from subprocess import PIPE, run

    try:
        result = run(["latex", "--version"], stdout=PIPE, stderr=PIPE, text=True)
        if result.returncode == 0:
            print("LaTeX installation found:")
            print(result.stdout.split("\n")[0])
            return True
        else:
            print("LaTeX installation found but may have issues:")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("LaTeX not found in PATH. Please check your LaTeX installation.")
        print(f"Current PATH: {os.environ['PATH']}")
        return False


def sanitize_latex(latex):
    """Remove LaTeX delimiters and prepare for rendering"""
    # Remove common LaTeX delimiters: \( \) or $ $
    return re.sub(r"\\[\(\)]|\$", "", latex)


def generate_unique_filename(latex, prefix="math_"):
    """Generate a unique filename based on the LaTeX content"""
    # Create a unique identifier based on the LaTeX content
    unique_id = str(uuid.uuid5(uuid.NAMESPACE_OID, latex))[:8]
    return f"{prefix}{unique_id}.svg"


def render_latex_to_svg(latex, output_path, dpi=300):
    """Render LaTeX expression to SVG image with inline dimensions"""
    # Clean the LaTeX expression
    clean_latex = sanitize_latex(latex)

    try:
        # Create figure with transparent background
        fig = plt.figure(figsize=(0.1, 0.1))  # Small initial size, will be adjusted
        fig.patch.set_alpha(0)  # Transparent background

        # Add text with LaTeX
        plt.text(0, 0, f"${clean_latex}$", fontsize=14)

        # Remove axes
        plt.axis("off")

        # Adjust figure size to fit the text
        plt.tight_layout(pad=0.1)

        # Save as SVG
        plt.savefig(
            output_path,
            format="svg",
            dpi=dpi,
            bbox_inches="tight",
            transparent=True,
            pad_inches=0.02,
        )
        plt.close(fig)

        return True
    except Exception as e:
        print(f"Error rendering LaTeX: {latex}")
        print(f"Error details: {e}")
        return False


def normalize_path(path):
    """Normalize path for EPUB (use forward slashes)"""
    return str(path).replace("\\", "/")


def get_epub_relative_path(file_path, content_root):
    """Get the path relative to the EPUB content root, normalized for EPUB"""
    rel_path = os.path.relpath(file_path, content_root)
    return normalize_path(rel_path)


def find_next_image_id(manifest_items):
    """Find the next available image ID number"""
    max_id = 0
    for item in manifest_items:
        item_id = item.get("id", "")
        if item_id.startswith("image"):
            try:
                num = int(item_id.replace("image", ""))
                max_id = max(max_id, num)
            except ValueError:
                continue
    return max_id + 1


def update_manifest(manifest_path, image_paths, content_root):
    """Update the EPUB manifest to include the generated SVG images"""
    try:
        print(f"Updating manifest at {manifest_path}")
        print(f"Content root: {content_root}")

        # Parse the OPF file
        tree = ET.parse(manifest_path)
        root = tree.getroot()

        # Handle namespaces in EPUB2
        # Extract namespace from root tag if present
        ns_match = re.match(r"\{(.*?)\}", root.tag)
        ns = ns_match.group(1) if ns_match else None

        # Find the manifest element
        if ns:
            manifest = root.find(f"{{{ns}}}manifest")
        else:
            manifest = root.find("manifest")

        if manifest is None:
            print("Error: Could not find manifest element in OPF file")
            return False

        # Get all existing item hrefs to avoid duplicates
        existing_hrefs = set()
        existing_items = manifest.findall("*")
        for item in existing_items:
            href = item.get("href")
            if href:
                existing_hrefs.add(normalize_path(href))

        # Find the next available image ID number
        next_image_id = find_next_image_id(existing_items)

        # Add new image items to manifest
        added_count = 0
        for img_path in image_paths:
            # Get relative path from content root to image
            rel_path = get_epub_relative_path(img_path, content_root)

            # Skip if this file is already in the manifest
            if rel_path in existing_hrefs:
                print(f"  Image already in manifest: {rel_path}")
                continue

            # Generate a unique ID for the item
            item_id = f"image{next_image_id:04d}"
            next_image_id += 1

            # Create new item element with the same namespace as other items
            if ns:
                item = ET.SubElement(manifest, f"{{{ns}}}item")
            else:
                item = ET.SubElement(manifest, "item")

            item.set("id", item_id)
            item.set("href", rel_path)
            item.set("media-type", "image/svg+xml")

            existing_hrefs.add(rel_path)
            added_count += 1
            print(f"  Added to manifest: {rel_path} with ID: {item_id}")

        # Write the updated manifest back to file
        tree.write(manifest_path, encoding="utf-8", xml_declaration=True)
        print(f"Successfully added {added_count} SVG images to the manifest")
        return True

    except Exception as e:
        print(f"Error updating manifest: {e}")
        import traceback

        traceback.print_exc()
        return False


def process_xhtml_file(
    xhtml_path, images_dir, manifest_path=None, content_root=None, image_prefix="math_"
):
    """Process XHTML file to extract and replace LaTeX expressions with inline SVG images"""
    # Ensure images directory exists
    Path(images_dir).mkdir(parents=True, exist_ok=True)

    # Read the XHTML file
    with open(xhtml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all LaTeX expressions - updated pattern to handle \( \) delimiters
    pattern = r'<span class="math notranslate nohighlight">(?:\\[\(\)]|\$)?(.*?)(?:\\[\(\)]|\$)?</span>'
    matches = re.findall(pattern, content, re.DOTALL)

    if not matches:
        print(f"No LaTeX expressions found in {xhtml_path}")
        return []

    print(f"Found {len(matches)} LaTeX expressions in {xhtml_path}")

    # Process each LaTeX expression
    replacements = []
    generated_images = []

    # Get all spans to ensure we're replacing the complete original content
    span_pattern = r'(<span class="math notranslate nohighlight">.*?</span>)'
    spans = re.findall(span_pattern, content, re.DOTALL)

    for span, latex in zip(spans, matches):
        # Generate a unique filename
        filename = generate_unique_filename(latex, image_prefix)
        image_path = os.path.join(images_dir, filename)

        # Render LaTeX to SVG
        success = render_latex_to_svg(latex, image_path)

        if success:
            # Add to list of generated images
            generated_images.append(os.path.abspath(image_path))

            # Create the image tag for EPUB2/Kindle with inline styling
            rel_path = os.path.relpath(images_dir, os.path.dirname(xhtml_path))
            image_tag = f'<img src="{normalize_path(os.path.join(rel_path, filename))}" alt="" style="vertical-align: middle; display: inline-block; height: 1.2em;" class="math-image"/>'

            # Store the original span and its replacement
            replacements.append((span, image_tag))

    # Apply all replacements
    for original, replacement in replacements:
        content = content.replace(original, replacement)

    # Add CSS for math images if not already present
    css_for_math = """
<style type="text/css">
.math-image {
  vertical-align: middle;
  display: inline-block;
  height: 1.2em;
  margin: 0;
  padding: 0;
}
</style>
"""
    if "<head>" in content and css_for_math not in content:
        content = content.replace("</head>", f"{css_for_math}</head>")

    # Write the modified content back to the file
    with open(xhtml_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully processed {xhtml_path}")
    print(f"Images saved to {images_dir}")

    return generated_images


def process_directory(
    xhtml_dir, images_dir, manifest_path=None, content_root=None, image_prefix="math_"
):
    """Process all XHTML files in a directory"""
    # Find all XHTML files in the directory
    xhtml_files = []
    for ext in ["*.xhtml", "*.html", "*.htm"]:
        xhtml_files.extend(glob.glob(os.path.join(xhtml_dir, ext)))

    if not xhtml_files:
        print(f"No XHTML files found in {xhtml_dir}")
        return

    print(f"Found {len(xhtml_files)} XHTML files to process")

    # Process each file
    all_generated_images = []
    for xhtml_path in tqdm(xhtml_files, desc="Processing files"):
        print(f"\nProcessing {os.path.basename(xhtml_path)}...")
        generated_images = process_xhtml_file(
            xhtml_path, images_dir, None, content_root, image_prefix
        )
        all_generated_images.extend(generated_images)

    # Update manifest if path was provided
    if manifest_path and all_generated_images and content_root:
        print(f"\nUpdating manifest with {len(all_generated_images)} images")
        update_manifest(manifest_path, all_generated_images, content_root)


def main():
    parser = argparse.ArgumentParser(
        description="Convert LaTeX expressions in XHTML files to SVG images for EPUB2/Kindle"
    )
    parser.add_argument(
        "xhtml_dir", help="Path to the directory containing XHTML files"
    )
    parser.add_argument(
        "images_dir", help="Path to the directory where images will be saved"
    )
    parser.add_argument(
        "--manifest", help="Path to the EPUB OPF manifest file to update"
    )
    parser.add_argument(
        "--content-root", help="Root directory of the EPUB content (for manifest paths)"
    )
    parser.add_argument("--prefix", default="math_", help="Prefix for image filenames")
    parser.add_argument("--latex-path", help="Path to LaTeX binaries if not in PATH")

    args = parser.parse_args()

    # Convert paths to absolute paths
    xhtml_dir = os.path.abspath(args.xhtml_dir)
    images_dir = os.path.abspath(args.images_dir)
    manifest_path = os.path.abspath(args.manifest) if args.manifest else None

    # Set custom LaTeX path if provided
    if args.latex_path:
        os.environ["PATH"] = f"{args.latex_path}:{os.environ.get('PATH', '')}"

    # Determine content root if not specified
    content_root = args.content_root
    if manifest_path and not content_root:
        # Try to find the OEBPS or content directory
        manifest_dir = os.path.dirname(manifest_path)
        if os.path.basename(manifest_dir) in ("OEBPS", "content"):
            content_root = manifest_dir
        else:
            # Go up one level if needed
            parent_dir = os.path.dirname(manifest_dir)
            if os.path.basename(parent_dir) in ("OEBPS", "content"):
                content_root = parent_dir
            else:
                content_root = manifest_dir

        print(f"Content root not specified, using: {content_root}")

    if content_root:
        content_root = os.path.abspath(content_root)

    # Check LaTeX installation before proceeding
    if check_latex_installation():
        process_directory(
            xhtml_dir, images_dir, manifest_path, content_root, args.prefix
        )
    else:
        print("\nAlternative: Try using a non-LaTeX renderer")
        use_non_latex = input("Continue with non-LaTeX renderer? (y/n): ")
        if use_non_latex.lower() == "y":
            # Fallback to non-LaTeX rendering
            matplotlib.rcParams.update(
                {
                    "text.usetex": False,
                    "mathtext.fontset": "stix",
                }
            )
            process_directory(
                xhtml_dir, images_dir, manifest_path, content_root, args.prefix
            )
        else:
            print("Exiting. Please check your LaTeX installation.")


if __name__ == "__main__":
    main()
