"""General-purpose training script for image-to-image translation.

This script works for various models (with option '--model': e.g., pix2pix, cyclegan, colorization) and
different datasets (with option '--dataset_mode': e.g., aligned, unaligned, single, colorization).
You need to specify the dataset ('--dataroot'), experiment name ('--name'), and model ('--model').

It first creates model, dataset, and visualizer given the option.
It then does standard network training. During the training, it also visualize/save the images, print/save the loss plot, and save models.
The script supports continue/resume training. Use '--continue_train' to resume your previous training.

Example:
    Train a CycleGAN model:
        python train.py --dataroot ./datasets/maps --name maps_cyclegan --model cycle_gan
    Train a pix2pix model:
        python train.py --dataroot ./datasets/facades --name facades_pix2pix --model pix2pix --direction BtoA

See options/base_options.py and options/train_options.py for more training options.
See training and test tips at: https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix/blob/master/docs/tips.md
See frequently asked questions at: https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix/blob/master/docs/qa.md
"""
import time
import torch
from ffwm.options.train_options import TrainOptions
from ffwm.data import create_dataset
from ffwm.models import create_model
from ffwm.util.visualizer import Visualizer
from collections import OrderedDict


def sum_loss(epoch_loss, batch_loss, iter):
    w = min(iter * opt.batch_size, dataset_size_train) - (iter - 1) * opt.batch_size
    if len(epoch_loss.keys()) == 0:
        for k in batch_loss:
            epoch_loss[k] = w * batch_loss[k]
    else:
        for k in batch_loss:
            epoch_loss[k] += w * batch_loss[k]
    return epoch_loss

if __name__ == '__main__':
    train_opt = TrainOptions()
    train_opt.parser.add_argument('--datamode', type=str, default='multipie', help='data mode: only multipie')
    train_opt.parser.add_argument('--reverse', action='store_true', help='true is the reverse flownet and false is the forward flownet')
    train_opt.parser.add_argument('--aug', action='store_true', help='data augment')
    opt = train_opt.parse()  # get training options
    dataset_train = create_dataset(opt, is_val=False)  # create a dataset given opt.dataset_mode
    dataset_size_train = len(dataset_train)  # get the number of images in the dataset.
    print('The number of training images = %d' % dataset_size_train)
    torch.set_num_threads(4)

    model = create_model(opt)  # create a model given opt.model
    model.setup(opt)  # regular setup: load and print networks; create schedulers
    model.reverse = opt.reverse
    visualizer = Visualizer(opt)  # create a visualizer that display/save images and plots
    total_iters = 0  # the total number of training iterations
    total_steps = 0
    for epoch in range(opt.epoch_count, opt.niter + opt.niter_decay + 1):
        epoch_start_time = time.time()  # timer for entire epoch
        iter_data_time = time.time()  # timer for data loading per iteration
        epoch_iter = 0  # the number of training iterations in current epoch, reset to 0 every epoch
        epoch_loss = OrderedDict()
        model.set_train()
        for i, data in enumerate(dataset_train):  # inner loop within one epoch
            iter_start_time = time.time()  # timer for computation per iteration
            if total_iters % opt.print_freq == 0:
                t_data = iter_start_time - iter_data_time
            visualizer.reset()
            total_iters += opt.batch_size
            epoch_iter += opt.batch_size
            data['titers'] = total_iters
            data['epoch'] = epoch
            model.set_input(data)  # unpack data from dataset and apply preprocessing
            model.optimize_parameters()  # calculate loss functions, get gradients, update network weights
            epoch_loss = sum_loss(epoch_loss, model.get_current_losses(), i + 1)
            if (i + 1) % opt.display_freq == 0:  # display images on visdom and save images to a HTML file
                save_result = True
                model.compute_visuals()
                visualizer.display_current_results(model.get_current_visuals(), epoch, save_result)
            if (i + 1) % opt.print_freq == 0:  # print training losses and save logging information to the disk
                losses = model.get_current_losses()
                total_steps += 1
                t_comp = (time.time() - iter_start_time) / opt.batch_size
                visualizer.print_current_losses(epoch, epoch_iter, losses, t_comp, t_data, total_steps)
            iter_data_time = time.time()
        model.save_networks('latest')
        if (epoch % opt.save_epoch_freq == 0 and opt.save_epoch_freq > 0):  # cache our model every <save_epoch_freq> epochs
            print('saving the model at the end of epoch %d, iters %d' % (epoch, total_iters))
            model.save_networks(epoch)
        for k in epoch_loss:
            epoch_loss[k] /= (dataset_size_train * 1.0)
        visualizer.print_current_losses(epoch, -1, epoch_loss, 0.0, 0.0, 0)
        print('End of epoch %d / %d \t Time Taken: %d sec' % (
            epoch, opt.niter + opt.niter_decay, time.time() - epoch_start_time))
        model.update_learning_rate()  # update learning rates at the end of every epoch.