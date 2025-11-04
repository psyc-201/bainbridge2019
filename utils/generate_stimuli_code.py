#!/usr/bin/env python3
"""
generate JS code for drawing loading
python generate_stimuli_code.py > stimuli_output.txt
"""

from pathlib import Path
from collections import defaultdict

CATEGORIES = [
    'amusementpark', 'badlands', 'bathroom', 'bedroom', 'diningroom',
    'farm', 'fountain', 'garden', 'house', 'kitchen', 'lighthouse',
    'livingroom', 'mountain', 'playground', 'pool', 'street', 'tower'
]

def parse_delayed_recall_filename(filename):
    """subnum]_[imnum]_[memorability]_[scene].jpg"""
    parts = filename.replace('.jpg', '').split('_')
    if len(parts) == 4:
        return {
            'memorability': parts[2],
            'scene': parts[3],
            'filename': filename
        }
    return None

def parse_category_filename(filename):
    """c[subnum]_[imnum]_[scene].jpg"""
    parts = filename.replace('.jpg', '').split('_')
    if len(parts) == 3 and parts[0].startswith('c'):
        return {
            'scene': parts[2],
            'filename': filename
        }
    return None

def main():
    project_root = Path.cwd()  
    delayed_dir = project_root / "data" / "drawings" / "delayed_recall"
    category_dir = project_root / "data" / "drawings" / "category"
    
    if not delayed_dir.exists():
        print("Error: run from project root")
        return
    
    delayed_by_category = defaultdict(lambda: {'high': None, 'low': None})
    for filepath in delayed_dir.glob('*.jpg'):
        parsed = parse_delayed_recall_filename(filepath.name)
        if parsed and parsed['scene'] in CATEGORIES:
            memorability = parsed['memorability']
            if memorability in ['high', 'low']:
                delayed_by_category[parsed['scene']][memorability] = parsed['filename']
    
    category_by_category = defaultdict(list)
    for filepath in category_dir.glob('*.jpg'):
        parsed = parse_category_filename(filepath.name)
        if parsed and parsed['scene'] in CATEGORIES:
            category_by_category[parsed['scene']].append(parsed['filename'])
    
    print("function generateDrawingStimuli() {")
    print("    const stimuli = [];")
    print()
    
    for category in CATEGORIES:
        print(f"    // {category.upper()}")
        
        # Delayed recall - high
        high_file = delayed_by_category[category]['high']
        if high_file:
            print(f"    stimuli.push({{")
            print(f"        drawing: '../data/drawings/delayed_recall/{high_file}',")
            print(f"        condition: 'delayed_recall',")
            print(f"        category: '{category}',")
            print(f"        target_image: '../data/stim/{category}_high.jpg',")
            print(f"        memorability: 'high',")
            print(f"        high_image: '../data/stim/{category}_high.jpg',")
            print(f"        low_image: '../data/stim/{category}_low.jpg',")
            print(f"        foil_image: '../data/stim/{category}_foil.jpg'")
            print(f"    }});")
        else:
            print(f"// !!!!!!no high-memorable delayed recall drawing found!!!!!")
        
        # Delayed recall - low
        low_file = delayed_by_category[category]['low']
        if low_file:
            print(f"    stimuli.push({{")
            print(f"        drawing: '../data/drawings/delayed_recall/{low_file}',")
            print(f"        condition: 'delayed_recall',")
            print(f"        category: '{category}',")
            print(f"        target_image: '../data/stim/{category}_low.jpg',")
            print(f"        memorability: 'low',")
            print(f"        high_image: '../data/stim/{category}_high.jpg',")
            print(f"        low_image: '../data/stim/{category}_low.jpg',")
            print(f"        foil_image: '../data/stim/{category}_foil.jpg'")
            print(f"    }});")
        else:
            print(f"// !!!no low-memorable delayed recall drawing found!!!")
        
        # Category drawings
        cat_files = category_by_category[category]
        if len(cat_files) >= 2:
            for cat_file in cat_files[:2]:  # Take first 2
                print(f"    stimuli.push({{")
                print(f"        drawing: '../data/drawings/category/{cat_file}',")
                print(f"        condition: 'category',")
                print(f"        category: '{category}',")
                print(f"        target_image: null,")
                print(f"        memorability: null,")
                print(f"        high_image: '../data/stim/{category}_high.jpg',")
                print(f"        low_image: '../data/stim/{category}_low.jpg',")
                print(f"        foil_image: '../data/stim/{category}_foil.jpg'")
                print(f"    }});")
        else:
            print(f"// less than 2 category drawings found ({len(cat_files)} available)")
        
        print()
    
    print("    return stimuli;")
    print("}")
    print()
    print(f"// total: {sum(2 if delayed_by_category[c]['high'] and delayed_by_category[c]['low'] else 0 for c in CATEGORIES) + sum(min(2, len(category_by_category[c])) for c in CATEGORIES)}")
    print("// Expected: 68 (34 delayed recall + 34 category)")

if __name__ == "__main__":
    main()