#!/usr/bin/env python3
"""
select drawings for the replication study. there are 17 categories total, 1 high-memorable delayed recall, 1 low-memorable delayed recall, 2 category drawings
in total: 68 drawings (34 delayed recall + 34 category)
"""

import os
import shutil
import random
from pathlib import Path
from collections import defaultdict

random.seed(42)

# took out the underscores because of naming convention
CATEGORIES = [
    'amusementpark', 'badlands', 'bathroom', 'bedroom', 'diningroom',
    'farm', 'fountain', 'garden', 'house', 'kitchen', 'lighthouse',
    'livingroom', 'mountain', 'playground', 'pool', 'street', 'tower'
]

DELAYED_RECALL_DIR = Path.home() / "Downloads" / "delayed-recall"
CATEGORY_DIR = Path.home() / "Downloads" / "category-drawings"
OUTPUT_DIR = Path.home() / "Desktop" / "selected-drawings"

def parse_delayed_recall_filename(filename):
    """delayed recall filename: [subnum]_[imnum]_[memorability]_[scene].jpg"""
    parts = filename.replace('.jpg', '').split('_')
    if len(parts) == 4:  
        return {
            'subnum': parts[0],
            'imnum': parts[1],
            'memorability': parts[2],
            'scene': parts[3], 
            'filename': filename
        }
    return None

def parse_category_filename(filename):
    """ category filename: c[subnum]_[imnum]_[scene].jpg"""
    parts = filename.replace('.jpg', '').split('_')
    if len(parts) == 3 and parts[0].startswith('c'):
        return {
            'subnum': parts[0],
            'imnum': parts[1],
            'scene': parts[2],
            'filename': filename
        }
    return None

def select_delayed_recall_drawings():
    """1 high and 1 low memorable drawing per category"""
    # group drawings by category and memorability
    drawings_by_category = defaultdict(lambda: {'high': [], 'low': []})
    
    for filename in os.listdir(DELAYED_RECALL_DIR):
        if not filename.endswith('.jpg'):
            continue
        
        parsed = parse_delayed_recall_filename(filename)
        if parsed and parsed['scene'] in CATEGORIES:
            memorability = parsed['memorability']
            if memorability in ['high', 'low']:
                drawings_by_category[parsed['scene']][memorability].append(filename)
    
    # randomly select 1 high and 1 low per category
    selected = []
    for category in CATEGORIES:
        high_drawings = drawings_by_category[category]['high']
        low_drawings = drawings_by_category[category]['low']
        
        if high_drawings:
            selected.append(random.choice(high_drawings))
        else:
            print(f"no high-memorable drawings found for {category}")
        
        if low_drawings:
            selected.append(random.choice(low_drawings))
        else:
            print(f"no low-memorable drawings found for {category}")
    
    return selected

def select_category_drawings():
    """2 category drawings per category"""
    # group drawings by category
    drawings_by_category = defaultdict(list)
    
    for filename in os.listdir(CATEGORY_DIR):
        if not filename.endswith('.jpg'):
            continue
        
        parsed = parse_category_filename(filename)
        if parsed and parsed['scene'] in CATEGORIES:
            drawings_by_category[parsed['scene']].append(filename)
    
    # randomly select 2 per category
    selected = []
    for category in CATEGORIES:
        available = drawings_by_category[category]
        
        if len(available) >= 2:
            selected.extend(random.sample(available, 2))
        elif len(available) == 1:
            selected.extend(available)
            print(f"Only 1 category drawing found for {category}")
        else:
            print(f"No category drawings found for {category}")
    
    return selected

def main():
    
    output_delayed = OUTPUT_DIR / "delayed_recall"
    output_category = OUTPUT_DIR / "category"
    output_delayed.mkdir(parents=True, exist_ok=True)
    output_category.mkdir(parents=True, exist_ok=True)
    
    print("\ndelayed recall drawings...")
    delayed_selected = select_delayed_recall_drawings()
    print(f"    selected {len(delayed_selected)} delayed recall drawings (target: 34)")

    print("\ncategory drawings...")
    category_selected = select_category_drawings()
    print(f"    selected {len(category_selected)} category drawings (target: 34)")
    
    # Copy files
    print("\ncopying")
    
    for filename in delayed_selected:
        src = DELAYED_RECALL_DIR / filename
        dst = output_delayed / filename
        shutil.copy2(src, dst)
    
    for filename in category_selected:
        src = CATEGORY_DIR / filename
        dst = output_category / filename
        shutil.copy2(src, dst)
    
    
    print("done!")
    print("\n Selected Delayed Recall drawings:")
    for f in sorted(delayed_selected):
        print(f"   {f}")
    
    print("\n Selected Category drawings:")
    for f in sorted(category_selected):
        print(f"   {f}")

if __name__ == "__main__":
    main()