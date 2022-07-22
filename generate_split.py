import argparse
from logging import exception
import random
import tarfile
import os.path

def parse_args(known=False):
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', type=int, default=20, help='split percentage, default 20%')
    parser.add_argument('--seed', type=int, default=0, help='randomizer seed, default 0')
    args = parser.parse_known_args()[0] if known else parser.parse_args()
    return args

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

def main(args):    
    default_path = '/home/sandro/Projects/License Plate/Neural Network/yolov5_custom_dataset/VOC_custom/ImageSets/Main/'
    line_count = 0
    rand_list = []
    train_range = 0
    split = args.split
    seed = args.seed

    with open(default_path + 'default.txt', 'r') as default_file:
        for line in default_file:          
            if line.strip():
                line_count += 1      
            rand_list.append(line_count)  

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

    try:
        make_tarfile('VOC_custom.tar.gz','VOC_custom')
        print('Generated archived dataset')
    except:
        print('Couldn\'t generate archived dataset') 

if __name__ == "__main__":
    args = parse_args()
    main(args)
