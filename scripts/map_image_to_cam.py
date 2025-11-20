import os
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path("labeling_annotations")
DRY_RUN = False

loc_to_id = {
    "fordham_road_hughes_avenue__nysdot-4616552": 4616552,
    "lenox_avenue_135_street__nysdot-4616578": 4616578,
    "atlantic_avenue_bqe__nysdot-4616456": 4616456,
    "atlantic_avenue_vanderbilt_avenue__nysdot-4616457": 4616457,
    "ocean_parkway_ditmas_avenue__nysdot-4616613": 4616613,
    "3_avenue_23_street__nysdot-4616409": 4616409,
    "9_avenue_49_street__nysdot-4616447": 4616447,
    "amsterdam_avenue_125_street__nysdot-4616453": 4616453,
    "canal_street_baxter_street__nysdot-4616502": 4616502,
    "church_street_park_pl__nysdot-4616507": 4616507,
    "houston_street_bowery_street__nysdot-4616573": 4616573,
    "hillside_avenue_little_neck_parkway__nysdot-4616571": 4616571
}

anno_to_id = {
    "label100cars_bx_fordham_annotations": 4616552,
    "label100cars_bx_lenox_annotations": 4616578,
    "label100cars_bk_atlbqe_annotations": 4616456,
}

def rename_images():
    if not BASE_DIR.exists():
        print(f"Base directory {BASE_DIR} does not exist.")
        exit

    for borough_dir in BASE_DIR.iterdir():
        if not borough_dir.is_dir():
            continue

        for loc_dir in borough_dir.iterdir():
            if not loc_dir.is_dir():
                continue

            loc_name = loc_dir.name
            cam_id = loc_to_id.get(loc_name)

            if cam_id is None:
                print(f"[WARN] No camera ID mapping for location folder: {loc_dir}")
                continue

            print(f"\n[INFO] Processing {loc_dir} (camera {cam_id})")

            for f in loc_dir.iterdir():
                if not f.is_file():
                    continue

                old_name = f.name

                # Skip already-prefixed files
                if old_name.startswith(f"{cam_id}__"):
                    print(f"  [SKIP] Already labeled: {old_name}")
                    continue

                new_name = f"{cam_id}__{old_name}"
                new_path = f.with_name(new_name)

                if new_path.exists():
                    print(f"  [SKIP] Target exists, not overwriting: {new_path.name}")
                    continue

                if DRY_RUN:
                    print(f"  [DRY RUN] Would rename: {old_name} -> {new_name}")
                else:
                    print(f"  [RENAME] {old_name} -> {new_name}")
                    f.rename(new_path)


def update_xml_file(xml_path: Path, cam_id: int):
    print(f"\n[INFO] Processing {xml_path} (camera {cam_id})")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # CVAT puts images under the root as <image ...>
    for image_el in root.findall(".//image"):
        old_name = image_el.get("name")
        if old_name is None:
            continue

        # Avoid double-prefixing: if it already starts with the same cam_id__, strip it
        base_name = old_name
        if old_name.startswith(f"{cam_id}__"):
            print(f"  [SKIP] Already in correct format: {old_name}")
            continue

        # if "__" in old_name:
        #     prefix, rest = old_name.split("__", 1)
        #     if prefix.isdigit():
        #         base_name = rest

        new_name = f"{cam_id}__{base_name}"

        print(f"  [RENAME] {old_name} -> {new_name}")
        if not DRY_RUN:
            image_el.set("name", new_name)

    if not DRY_RUN:
        backup_path = xml_path.with_suffix(xml_path.suffix + ".bak")
        if not backup_path.exists():
            xml_path.replace(backup_path)
            print(f"  [BACKUP] Original saved as {backup_path.name}")
            # write to original name
            tree.write(xml_path, encoding="utf-8", xml_declaration=True)
            print(f"  [WRITE] Updated XML written to {xml_path.name}")
        else:
            # If backup exists, just overwrite the current file
            tree.write(xml_path, encoding="utf-8", xml_declaration=True)
            print(f"  [WRITE] Updated XML overwritten (backup already exists)")


# UNCOMMENT TO RENAME IMAGES
# rename_images()

# UNCOMMENT TO RENAME XML
for anno_base, cam_id in anno_to_id.items():
    xml_path = BASE_DIR / f"{anno_base}.xml"
    if not xml_path.exists():
        print(f"[WARN] XML file not found: {xml_path}")
        continue
    update_xml_file(xml_path, cam_id)


