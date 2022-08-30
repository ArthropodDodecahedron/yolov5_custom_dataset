import argparse
from logging import exception
import random
import tarfile
import os.path
import zipfile
import shutil
from coco2voc import convert

def parse_args(known=False):
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, help='source archive(s), required', nargs='+', required=True)
    parser.add_argument('--split', type=int, default=20, help='split percentage, default 20%')
    parser.add_argument('--seed', type=int, default=0, help='randomizer seed, default 0')
    parser.add_argument('--arch', type=int, default=False, help='make an archive, default false')
    args = parser.parse_known_args()[0] if known else parser.parse_args()
    return args

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

def unpack_zipfile(source_zipfile, dest_dir):
    with zipfile.ZipFile(source_zipfile, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)

def check_format(temp_path, source):
    if os.path.exists(temp_path + '/labelmap.txt'):
        print('Detected VOC format dataset')
        return('VOC') 
    elif os.path.exists(temp_path + '/annotations/instances_default.json'):
        print('Detected COCO format dataset')
        return('COCO')
    else:
        raise Exception('Unknown format: ' + str(source))

def main(args):    
    workdir_path = os.getcwd() 
    dataset_dir = 'VOC_custom'
    line_count = 0
    rand_list = []
    train_range = 0
    split = args.split
    seed = args.seed
    arch = args.arch
    source = args.source
    
    ### Delete existing dataset directory
    shutil.rmtree(dataset_dir)

    VOC_path = os.path.join(workdir_path, dataset_dir)
    os.mkdir(VOC_path)
  
    ### Create temp directories for each source file
    for i in range(len(source)):
        temp_directory = source[i] + '_temp'
        temp_path = os.path.join(VOC_path, temp_directory)
        os.mkdir(temp_path)
        unpack_zipfile(source[i],temp_path)

        ### Check format and convert to VOC
        if check_format(temp_path, source[i]) == 'COCO':
            voc_dirs = ['Annotations','JPEGImages','ImageSets','Main']
            xml_path = os.path.join(temp_path, voc_dirs[0])
            jpeg_path = os.path.join(temp_path, voc_dirs[1])
            txt_path = os.path.join(temp_path, voc_dirs[2])
            main_path = os.path.join(temp_path, voc_dirs[2], voc_dirs[3])
            os.mkdir(xml_path)
            os.mkdir(jpeg_path)
            os.mkdir(txt_path)
            os.mkdir(main_path)
            convert(temp_path + '/annotations/instances_default.json', xml_path)
            file_names_JPEG = os.listdir(temp_path + '/images') 
            for file in file_names_JPEG:
                shutil.move(temp_path + '/images/' + file, jpeg_path)
            with open(main_path + '/default.txt', 'w') as coco_default:
                for i in range(len(file_names_JPEG)):
                    coco_default.write(file_names_JPEG[i].replace('.jpeg','').replace('.jpg','') + '\n')
            shutil.rmtree(temp_path + '/annotations')
            shutil.rmtree(temp_path + '/images')

        ### Remove white spaces from filenames and .txt's
        with open(temp_path + '/ImageSets/Main/default.txt', "r+") as default_file:
            default_text = default_file.read()
            default_file.seek(0)
            for line in default_text:
                line = line.replace(' ','_')
                default_file.write(line)           
            default_file.truncate()
        file_names_JPEG = os.listdir(temp_path + '/JPEGImages')           
        file_names_annotations = os.listdir(temp_path + '/Annotations')
        for file_name in file_names_JPEG:
            os.rename(temp_path + '/JPEGImages/' + file_name, temp_path + '/JPEGImages/' + file_name.replace(' ','_'))
        for file_name in file_names_annotations:
            os.rename(temp_path + '/Annotations/' + file_name, temp_path + '/Annotations/' + file_name.replace(' ','_'))
    
    ### Merge directories
    ### Move contents of the first source into the main dataset directory
    first_source_dir = source[0] + '_temp'
    source_dir = os.path.join(VOC_path, first_source_dir)
    list_dir = os.listdir(source_dir)
    L = ['Annotations', 'ImageSets', 'JPEGImages']
    for sub_dir in list_dir:
        if sub_dir in L:
            dir_to_move = os.path.join(source_dir, sub_dir)
            shutil.move(dir_to_move, VOC_path)
    shutil.move(source_dir + '/labelmap.txt', VOC_path + '/labelmap.txt')
    ### Remove source directory
    shutil.rmtree(VOC_path + '/' + source[0] + '_temp')

    ### Add contents of other directories
    for i in range(1, len(source)):
        ### Modify .txt with list of files
        with open(VOC_path + '/' + source[i] + '_temp/ImageSets/Main/default.txt', 'r') as file_source:
            for line in file_source:          
                with open(VOC_path + '/ImageSets/Main/default.txt', 'a') as file_dest:
                    file_dest.write(line)
        ### Move contents of annotations and jpegs
        source_dir_JPEG =  VOC_path + '/' + source[i] + '_temp/JPEGImages'
        source_dir_annotations =  VOC_path + '/' + source[i] + '_temp/Annotations'
        file_names_JPEG = os.listdir(source_dir_JPEG)           
        file_names_annotations = os.listdir(source_dir_annotations)
        for file in file_names_JPEG:
            shutil.move(os.path.join(source_dir_JPEG, file), VOC_path + '/JPEGImages')
        for file in file_names_annotations:
            shutil.move(os.path.join(source_dir_annotations, file), VOC_path + '/Annotations')
        ### Remove source directory
        shutil.rmtree(VOC_path + '/' + source[i] + '_temp')
        
    ## Generate split
    default_path = workdir_path + '/VOC_custom/ImageSets/Main/'
    with open(default_path + 'default.txt', 'r') as default_file:
        for line in default_file:          
            if line.strip():
                line_count += 1      
            rand_list.append(line.rstrip())  

    random.seed(seed)
    random.shuffle(rand_list)
    train_range = line_count - int((line_count*split)/100)
    test_range = line_count - train_range

    with open(default_path + 'train.txt', 'w') as train_file:       
        if split < 1 or split > 99:
            raise ValueError('Split percentage must be within 1-99 range')
        else:
            try:               
                print(train_range)
                for i in range(train_range):
                    train_file.write(str(rand_list[i]) + '\n')
                print('Finished generating split dataset')
            except:
                print('Couldn\'t write to file')
    
    with open(default_path + 'test.txt', 'w') as test_file:
        try:
            for i in range(train_range,train_range + test_range):
                test_file.write(str(rand_list[i]) + '\n')
            print('Finished generating test dataset')
        except:
            print('Couldn\'t write to file')

    print('Total number of images in the dataset: ' + str(line_count))
    print('Number of images in the train dataset: ' + str(train_range))
    print('Number of images in the test dataset: ' + str(test_range)) 
	
    if arch == True:
        try:
            make_tarfile('VOC_custom.tar.gz','VOC_custom')
            print('Generated archived dataset')
        except:
            print('Couldn\'t generate archived dataset') 

if __name__ == "__main__":
    args = parse_args()
    main(args)
