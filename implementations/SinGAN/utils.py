
import torch
import torch.nn as nn
import torch.optim as optim
import torch.autograd as autograd
from torch.autograd import grad, Variable
from torchvision.utils import save_image
import numpy as np

from .model import Generator, Discriminator
from ..general import save_args

def load_real(
    image_path, device,
    max_size=250, min_size=25, scale_factor=0.75, save_samples=True
):
    
    sizes = []
    tmp_size = max_size
    while tmp_size > min_size:
        tmp_size = round(max_size * scale_factor ** len(sizes))
        sizes.append(tmp_size)
    sizes = sorted(sizes)

    import torchvision.transforms as T
    def get_transform(size):
        return T.Compose([
            T.Resize(size),
            T.ToTensor(),
            T.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
        ])
    
    from PIL import Image
    reals = []
    xy_sizes = []
    image = Image.open(image_path).convert('RGB')
    for size in sizes:
        # prepair real image for a scale
        transform = get_transform(size)
        trans_image = transform(image)
        trans_image = trans_image.view(1, *trans_image.size())
        trans_image = trans_image.to(device)
        reals.append(trans_image)
        # get size of transformed image
        xy_sizes.append((trans_image.size(2), trans_image.size(3)))

        if save_samples:
            save_image(reals[-1], './SinGAN/result/sample_{}x{}.png'.format(*xy_sizes[-1]), normalize=True)
    
    return reals, xy_sizes

def test_sizes(max_size, num_scale, scale_factor, width_scale=1):
    sizes = []
    for scale in range(num_scale):
        sizes.append((round(max_size *scale_factor ** scale), round((max_size * scale_factor ** scale) * width_scale)))
    return sorted(sizes)

def calc_gradient_penalty_one(D, real_image, fake_image, device):
    alpha = torch.from_numpy(np.random.random((real_image.size(0), 1, 1, 1)))
    alpha = alpha.type(torch.FloatTensor).to(device)

    interpolates = (alpha * real_image + ((1 - alpha) * fake_image)).requires_grad_(True)
    d_interpolates = D.forward(interpolates)

    fake = torch.Tensor(d_interpolates.size()).fill_(1.).requires_grad_(False)
    fake = fake.type(torch.FloatTensor).to(device)

    gradients = autograd.grad(
        outputs=d_interpolates,
        inputs=interpolates,
        grad_outputs=fake,
        create_graph=True,
        retain_graph=True,
        only_inputs=True
    )[0]
    gradients = gradients.view(gradients.size(0), -1)
    penalty = ((gradients.norm(2, dim=1) - 1) ** 2).mean()

    return penalty


def calc_gradient_penalty_zero(D, real_image):
    loc_real_image = Variable(real_image, requires_grad=True)
    gradients = grad(
        outputs=D.forward(loc_real_image)[:, 0].sum(),
        inputs=loc_real_image,
        create_graph=True, retain_graph=True
    )[0]
    gradients = gradients.view(gradients.size(0), -1)
    gradients = (gradients ** 2).sum(dim=1).mean()
    return gradients / 2

def train(
    epochses, G_step, D_step,
    G, D,
    reals, test,
    lr, betas,
    rec_criterion, gp_type,
    gp_lambda, rec_alpha,
    save_interval, verbose_interval
):

    if gp_type == 'one':
        def empty(x):
            return x
        out_func = empty
    elif gp_type == 'zero':
        out_func = nn.Softplus()
    else:
        raise Exception('no such type \'{}\'.'.format(gp_type))

    for scale, epochs in enumerate(epochses):
        print('Scale {:2} / {:2}'.format(scale+1, len(epochses)))

        # optimizers
        optimizer_G = optim.Adam(G.parameters(), lr=lr, betas=betas)
        optimizer_D = optim.Adam(D.parameters(), lr=lr, betas=betas)
        # schedular

        for epoch in range(1, epochs+1):
            '''
            Discriminator
            '''
            for j in range(D_step):
                # D(x)
                real_prob = D.forward(reals[scale])
                real_loss = out_func(- real_prob).mean()
                # D(G(z))
                fake = G.forward()
                fake_prob = D.forward(fake.detach())
                fake_loss = out_func(fake_prob).mean()
                # gradient penalty
                if gp_type == 'zero':
                    gp = calc_gradient_penalty_zero(D, reals[scale])
                elif gp_type == 'one':
                    gp = calc_gradient_penalty_one(D, reals[scale], fake, device=D.device)
                # total
                D_loss = real_loss + fake_loss + gp * gp_lambda

                # optimization
                optimizer_D.zero_grad()
                D_loss.backward(retain_graph=True)
                optimizer_D.step()

            '''
            Generator
            '''
            for j in range(G_step):
                # D(G(z))
                fake = G.forward()
                real_prob = D.forward(fake)
                real_loss = out_func(- real_prob).mean()
                # reconstruction loss
                rec_fake = G.forward(rec=True)
                rec_loss = rec_criterion(rec_fake, reals[scale])
                # total
                G_loss = real_loss + rec_loss * rec_alpha

                # optimization
                optimizer_G.zero_grad()
                G_loss.backward(retain_graph=True)
                optimizer_G.step()


            if epoch % verbose_interval == 0:
                print('{:3} / {:3} [G : {:.5f}] [D : {:.5f}]'.format(epoch, epochs, G_loss.item(), D_loss.item()))
            if epoch % save_interval == 0:
                save_image(fake, './SinGAN/result/{}_{}.png'.format(scale, epoch), normalize=True, range=(-1, 1))

        if scale+1 < len(epochses):
            G.progress(rec_fake, reals[scale])
            D.progress()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    # G.cpu()
    if test:
        G.eval(all=True)
        img = G.forward(sizes=test)
        save_image(img, './implementations/SinGAN/result/eval_{}x{}.png'.format(*test[-1]), normalize=True, range=(-1, 1))

def add_arguments(parser):
    parser.add_argument('--image-path', default='./data/animefacedataset/images/63568_2019.jpg', type=str, help='path to image')
    parser.add_argument('--max-size', default=220, type=int, help='max size when training')
    parser.add_argument('--min-size', default=25,  type=int, help='min size when training')
    parser.add_argument('--scale-factor', default=0.7, type=float, help='scaling factor for resing the traning image')
    parser.add_argument('--save-real', default=False, action='store_true', help='save real samples')
    parser.add_argument('--img-channels', default=3, type=int, help='image channel size')
    parser.add_argument('--channels', default=32, type=int, help='channels width multiplier')
    parser.add_argument('--kernel-size', default=3, type=int, help='kernel size for convolution layers')
    parser.add_argument('--norm-layer', default='bn', choices=['bn', 'in', 'sn'], help='normalization layer name')
    parser.add_argument('--num-layers', default=5, type=int, help='number of layers for each scale G')
    parser.add_argument('--disable-img-out', default=False, action='store_true', help='no tanh() on output of G')
    parser.add_argument('--disable-bias', default=False, action='store_true', help='do not use bias')

    parser.add_argument('--epochs', default=3000, type=int, help='epochs to train for each scale')
    parser.add_argument('--increase', default=0, type=int, help='epochs to increase in each scale')
    parser.add_argument('--G-step', default=3, type=int, help='number of steps for G before updating D')
    parser.add_argument('--D-step', default=3, type=int, help='number of steps for D before updating G')
    parser.add_argument('--lr', default=0.0005, type=float, help='learning rate')
    parser.add_argument('--beta1', default=0.5, type=float, help='beta1')
    parser.add_argument('--beta2', default=0.999, type=float, help='beta2')
    parser.add_argument('--gp-type', default='one', choices=['one', 'zero'], help='center for gradient penalty')
    parser.add_argument('--gp-lambda', default=0.1, type=float, help='lambda for gradient penalty')
    parser.add_argument('--rec-alpha', default=10., type=float, help='alpha for reconstruction loss')
    parser.add_argument('--test-size', default=500, type=int, help='size of test image')
    return parser

def main(parser):

    parser = add_arguments(parser)
    args = parser.parse_args()
    save_args(args)
    
    img_out = not args.disable_img_out
    bias = not args.disable_bias
    betas = (args.beta1, args.beta2)


    if not args.disable_gpu:
        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device('cpu')

    reals, sizes = load_real(
        args.image_path, device, args.max_size, args.min_size,
        args.scale_factor, args.save_real)
    # test = test_sizes(test_size, len(sizes), scale_factor)
    test = None

    Gs = Generator(
        sizes, device, args.img_channels, args.channels,
        args.kernel_size, args.norm_layer, args.num_layers, img_out, bias=bias)
    Ds = Discriminator(
        sizes, device, args.img_channels, args.channels,
        args.kernel_size, args.norm_layer, args.num_layers, bias=bias)
    Gs.to()
    Ds.to()

    rec_criterion = nn.MSELoss()

    train(
        [args.epochs + scale*args.increase for scale, _ in enumerate(sizes)], args.G_step, args.D_step,
        Gs, Ds,
        reals, test,
        args.lr, betas,
        rec_criterion, args.gp_type,
        args.gp_lambda, args.rec_alpha,
        1000, 1000
    )
