"""
Adapted from https://github.com/vietnguyen91/QuickDraw/blob/master/src/dataset.py
@author: Viet Nguyen <nhviet1009@gmail.com>
"""
from torch.utils.data import Dataset
import numpy as np

CLASSES = (
            'face',
            'moustache',
            'pear',
            'umbrella',
            'pineapple',
            'mouth',
            'nose',
            'wine bottle',
            'apple',
            'octopus'
        )

class QuickdrawDataset(Dataset):
    def __init__(self, root_path="data", total_images_per_class=20000, ratio=0.8, mode="train", transform=None):
        self.root_path = root_path
        self.num_classes = len(CLASSES)
        self.images = [None] * (self.num_classes * total_images_per_class)
        self.transform = transform
        if mode == "train":
            self.offset = 0
            self.num_images_per_class = int(total_images_per_class * ratio)

        else:
            self.offset = int(total_images_per_class * ratio)
            self.num_images_per_class = int(total_images_per_class * (1 - ratio) + 1)
        self.num_samples = self.num_images_per_class * self.num_classes

        iterator = 0
        for (classidx, classname) in enumerate(CLASSES):
            file_ = "{}/full_numpy_bitmap_{}.npy".format(self.root_path, classname)
            classimages = np.load(file_).astype(np.float32)[self.offset : self.offset + self.num_images_per_class]
            classimages /= 255
            classimages = classimages.reshape((self.num_images_per_class, 1, 28, 28))
            print("loading classname ", classname, " and its shape is ", classimages.shape)
            self.images[(classidx * self.num_images_per_class) : ((1 + classidx) * self.num_images_per_class)] = classimages
            

    def __len__(self):
        return self.num_samples

    def __getitem__(self, item):
        # file_ = "{}/full_numpy_bitmap_{}.npy".format(self.root_path, CLASSES[int(item / self.num_images_per_class)])
        # image = np.load(file_).astype(np.float32)[self.offset + (item % self.num_images_per_class)]
        # image /= 255
        # return image.reshape((1, 28, 28)), int(item / self.num_images_per_class)
        if self.transform:
            # print("BEFORE, the image was ", self.images[item].shape)
            image = self.transform(self.images[item])
            # print("AFTER, the image is ", image.shape)
            return item, int(item / self.num_images_per_class)
        else:
            return self.images[item], int(item / self.num_images_per_class)


if __name__ == "__main__":
    training_set = QuickdrawDataset("data", 500, 0.8, "test")
    print(training_set.__getitem__(3))