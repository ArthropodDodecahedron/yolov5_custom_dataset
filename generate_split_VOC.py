import argparse
from logging import exception
import random
import tarfile
import os.path
import zipfile
import shutil

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

    ### Merge sources if more than 1
    if(len(source)) > 1:
        ### Create temp directories for each source file
        for i in range(len(source)):
            temp_directory = source[i] + '_temp'
            temp_path = os.path.join(VOC_path, temp_directory)
            os.mkdir(temp_path)
            unpack_zipfile(source[i],temp_path)

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
