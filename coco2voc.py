# pip install pycocotools
import os
import time
import json
import pandas as pd
from tqdm import tqdm
from pycocotools.coco import COCO
import argparse





def parse_args(known=False):
    parser = argparse.ArgumentParser()
    parser.add_argument('--anno', type=str, help='annotation source', required=True)
    parser.add_argument('--xml_dir', type=int, help='xml destination', required=True)
    args = parser.parse_known_args()[0] if known else parser.parse_args()
    return args

def trans_id(category_id,cats):
    names = []
    namesid = []
    for i in range(0, len(cats)):
        names.append(cats[i]['name'])
        namesid.append(cats[i]['id'])
    index = namesid.index(category_id)
    return index

def convert(anno,xml_dir): 
    coco = COCO(anno)  # read file
    cats = coco.loadCats(coco.getCatIds())  # Here, loadCats is the interface provided by coco to obtain categories
    with open(anno, 'r') as load_f:
        f = json.load(load_f)
    
    imgs = f['images']  #IMG of json file_ How many images does the imgs list represent
    
    cat = f['categories']
    df_cate = pd.DataFrame(f['categories'])                     # Categories in json
    df_cate_sort = df_cate.sort_values(["id"], ascending=True)  # Sort by category id
    categories = list(df_cate_sort['name'])                     # Get all category names
    print('categories = ', categories)
    df_anno = pd.DataFrame(f['annotations'])                    # annotation in json
    
    for i in tqdm(range(len(imgs))):  # The large loop is all images, and Tqdm is an extensible Python progress bar. You can add a progress prompt to the long loop
        xml_content = []
        file_name = imgs[i]['file_name']    # Through img_id find the information of the picture
        height = imgs[i]['height']
        img_id = imgs[i]['id']
        width = imgs[i]['width']
        
        version =['"1.0"','"utf-8"'] 
    
        # Add attributes to xml file
        xml_content.append("<?xml version=" + version[0] +" "+ "encoding="+ version[1] + "?>")
        xml_content.append("<annotation>")
        xml_content.append("    <filename>" + file_name + "</filename>")
        xml_content.append("    <size>")
        xml_content.append("        <width>" + str(width) + "</width>")
        xml_content.append("        <height>" + str(height) + "</height>")
        xml_content.append("        <depth>"+ "3" + "</depth>")
        xml_content.append("    </size>")
    
        # Through img_id found annotations
        annos = df_anno[df_anno["image_id"].isin([img_id])]  # (2,8) indicates that a drawing has two boxes
    
        for index, row in annos.iterrows():  # All annotation information of a graph
            bbox = row["bbox"]
            category_id = row["category_id"]
            cate_name = categories[trans_id(category_id,cats)]
    
            # add new object
            xml_content.append("    <object>")
            xml_content.append("        <name>" + cate_name + "</name>")
            xml_content.append("        <truncated>0</truncated>")
            xml_content.append("        <difficult>0</difficult>")
            xml_content.append("        <bndbox>")
            xml_content.append("            <xmin>" + str(int(bbox[0])) + "</xmin>")
            xml_content.append("            <ymin>" + str(int(bbox[1])) + "</ymin>")
            xml_content.append("            <xmax>" + str(int(bbox[0] + bbox[2])) + "</xmax>")
            xml_content.append("            <ymax>" + str(int(bbox[1] + bbox[3])) + "</ymax>")
            xml_content.append("        </bndbox>")
            xml_content.append("    </object>")
        xml_content.append("</annotation>")
    
        x = xml_content
        xml_content = [x[i] for i in range(0, len(x)) if x[i] != "\n"]
        ### list save file
        #xml_path = os.path.join(xml_dir, file_name.replace('.xml', '.jpg'))
        xml_path = os.path.join(xml_dir, file_name.split('j')[0]+'xml')
        print(xml_path)
        with open(xml_path, 'w+', encoding="utf8") as f:
            f.write('\n'.join(xml_content))
        xml_content[:] = []

def main(args):
    anno = args.anno
    xml_dir = args.xml_dir

    
    # Create anno dir
    dttm = time.strftime("%Y%m%d%H%M%S", time.localtime())
    convert(anno,xml_dir)

if __name__ == "__main__":
    args = parse_args()
    main(args)