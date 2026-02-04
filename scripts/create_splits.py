import argparse
import copy
import random
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xmls", nargs="+", required=True, help="List of CVAT annotations.xml files")
    ap.add_argument("--out", default="splits_out", help="Output directory")
    ap.add_argument("--seed", type=int, default=42, help="Shuffle seed")
    ap.add_argument("--train", type=float, default=0.8, help="Train ratio")
    ap.add_argument("--val", type=float, default=0.1, help="Val ratio")
    ap.add_argument("--test", type=float, default=0.1, help="Test ratio")
    return ap.parse_args()

def write_cvat_xml(out_path: Path, meta_root, version_text, images):
    root = ET.Element("annotations")
    if version_text is not None:
        v = ET.SubElement(root, "version")
        v.text = version_text
    if meta_root is not None:
        root.append(copy.deepcopy(meta_root))

    for _, img_el in images:
        root.append(img_el)

    ET.indent(root, space="  ", level=0)
    tree = ET.ElementTree(root)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)

def main():
    args = parse_args()
    ratios = (args.train, args.val, args.test)
    if abs(sum(ratios) - 1.0) > 1e-6:
        raise ValueError("train+val+test must sum to 1.0")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    image_records = []
    meta_root = None
    version_text = None

    for xml_path in args.xmls:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Use the first file's meta/version
        if meta_root is None:
            version_el = root.find("version")
            version_text = version_el.text if version_el is not None else None
            meta = root.find("meta")
            meta_root = copy.deepcopy(meta) if meta is not None else None

        for img in root.findall("image"):
            name = img.get("name")
            image_records.append((name, copy.deepcopy(img)))

    if not image_records:
        raise RuntimeError("No <image> entries found in the provided XMLs.")

    # sanity: duplicates
    names = [n for n, _ in image_records]
    if len(names) != len(set(names)):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise RuntimeError(f"Duplicate image names found (first few): {dupes[:10]}")

    rng = random.Random(args.seed)
    rng.shuffle(image_records)

    n = len(image_records)
    n_train = round(args.train * n)
    n_val = round(args.val * n)
    if n_train + n_val > n:
        n_val = n - n_train
    n_test = n - n_train - n_val

    splits = {
        "train": image_records[:n_train],
        "val": image_records[n_train:n_train + n_val],
        "test": image_records[n_train + n_val:],
    }

    for split_name, items in splits.items():
        write_cvat_xml(out_dir / f"{split_name}_annotations.xml", meta_root, version_text, items)
        with open(out_dir / f"{split_name}_images.txt", "w", encoding="utf-8") as f:
            for name, _ in items:
                f.write(name + "\n")

    print(f"Total images: {n}")
    print(f"Train/Val/Test: {len(splits['train'])}/{len(splits['val'])}/{len(splits['test'])}")
    print(f"Wrote outputs to: {out_dir.resolve()}")

if __name__ == "__main__":
    main()

