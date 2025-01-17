
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import grad, Variable
from torch.cuda.amp import autocast, GradScaler
from torchvision import models
import torchvision.transforms.functional as TF

'''
Base
'''

class Loss:
    '''base class for every loss'''
    def __init__(self, backward=False, return_all=False):
        '''
        args
            backward : bool (default:False)
                if True, .backward() is called before return
            return_all : bool (default:False)
                if True, returns partial calculation results of the total loss if exists (e.g. real_loss, fake_loss in d_loss)
        '''
        self.backward = backward
        self.return_all = return_all


class AdversarialLoss(Loss):
    '''base class for adversarial loss'''
    def d_loss(self, real_prob, fake_prob):
        '''calculates loss for discriminator

        args
            real_prob : torch.Tensor
                D(x)
            fake_prob : torch.Tensor
                D(G(z))
        '''
        raise NotImplementedError()
    def g_loss(self, fake_prob):
        '''calculates loss for generator

        args
            fake_prob : torch.Tensor
                D(G(z))
        '''
        raise NotImplementedError()


'''
Adversarial Loss
'''

class GANLoss(AdversarialLoss):
    '''original GAN loss'''
    def d_loss(self, real_prob, fake_prob):
        '''Ld = E[log(D(x)) + log(1 - D(G(z)))]'''
        real_loss = F.softplus(- real_prob).mean()
        fake_loss = F.softplus(  fake_prob).mean()

        adv_loss = real_loss + fake_loss

        if self.backward:
            adv_loss.backward(retain_graph=True)

        if self.return_all:
            return adv_loss, real_loss, fake_loss
        return adv_loss
    def g_loss(self, fake_prob):
        '''Lg = E[log(D(G(z)))]'''
        fake_loss = F.softplus(- fake_prob).mean()

        if self.backward:
            fake_loss.backward(retain_graph=True)
        
        return fake_loss


class LSGANLoss(AdversarialLoss):
    '''lsgan loss (a,b,c = 0,1,1)'''
    def d_loss(self, real_prob, fake_prob):
        '''Ld = 1/2*E[(D(x) - 1)^2] + 1/2*E[D(G(z))^2]'''
        real_loss = F.mse_loss(real_prob, torch.ones(real_prob.size(), device=real_prob.device))
        fake_loss = F.mse_loss(fake_prob, torch.zeros(fake_prob.size(), device=fake_prob.device))

        adv_loss = (real_loss + fake_loss) / 2

        if self.backward:
            adv_loss.backward(retain_graph=True)

        if self.return_all:
            return adv_loss, real_loss, fake_loss
        return adv_loss
    def g_loss(self, fake_prob):
        '''Lg = 1/2*E[(D(G(z)) - 1)^2]'''
        fake_loss = F.mse_loss(fake_prob, torch.ones(fake_prob.size(), device=fake_prob.device))
        fake_loss = fake_loss / 2

        if self.backward:
            fake_loss.backward(retain_graph=True)
        
        return fake_loss

class WGANLoss(AdversarialLoss):
    '''wgan loss'''
    def d_loss(self, real_prob, fake_prob):
        '''Ld = E[D(G(z))] - E[D(x)]'''
        real_loss = - real_prob.mean()
        fake_loss =   fake_prob.mean()

        adv_loss = real_loss + fake_loss

        if self.backward:
            adv_loss.backward(retain_graph=True)

        if self.return_all:
            return adv_loss, real_loss, fake_loss
        return adv_loss
    def g_loss(self, fake_prob):
        '''Lg = -E[D(G(z))]'''
        fake_loss = - fake_prob.mean()

        if self.backward:
            fake_loss.backward(retain_graph=True)

        return fake_loss

class HingeLoss(AdversarialLoss):
    '''hinge loss'''
    def d_loss(self, real_prob, fake_prob):
        '''Ld = - E[min(0, 1 + D(x))] - E[min(0, -1 - D(G(z)))]'''
        real_loss = F.relu(1. - real_prob).mean()
        fake_loss = F.relu(1. + fake_prob).mean()

        adv_loss = real_loss + fake_loss

        if self.backward:
            adv_loss.backward(retain_graph=True)

        if self.return_all:
            return adv_loss, real_loss, fake_loss
        return adv_loss
    def g_loss(self, fake_prob):
        '''Lg = - E[D(G(z))]'''
        fake_loss = - fake_prob.mean()

        if self.backward:
            fake_loss.backward(retain_graph=True)

        return fake_loss


'''
Regularization
'''

class GradPenalty(Loss):
    def _calc_grad(self, outputs, inputs, scaler=None):
        '''calculate gradients

        args
            outputs: torch.Tensor
                output tensor of a model
            inputs: torch.Tensor
                input tensor to a model
            scaler: torch.cuda.amp.GradScaler (default: None)
                gradient scaler if using torch.cuda.amp
        '''
        with autocast(False):
            if isinstance(scaler, GradScaler):
                outputs = scaler.scale(outputs)
            ones = torch.ones(outputs.size(), device=outputs.device)
            gradients = grad(
                outputs=outputs,
                inputs=inputs,
                grad_outputs=ones,
                create_graph=True,
                retain_graph=True,
                only_inputs=True
            )[0]
            if isinstance(scaler, GradScaler):
                gradients = gradients / scaler.get_scale()
        return gradients

    def gradient_penalty(self, real, fake, D, scaler=None, center=1.):
        '''calculate gradient penalty (1 and 0 center)

        args
            real: torch.Tensor
                batched tensor of real images
            fake: torch.Tensor
                generated image tensor
            D: torch.nn.Module
                discriminator to calculate the gradient for
            scaler: torch.cuda.amp.GradScaler (default: None)
                gradient scaler for torch.cuda.amp
            center: Union[int, float] (default: 1.)
                the center used the calculate the penalty
        '''
        assert center in [1., 0., 1, 0]

        device = real.device

        alpha = torch.rand(1, device=device)
        x_hat = real * alpha + fake * (1 - alpha)
        x_hat = Variable(x_hat, requires_grad=True)

        d_x_hat = D(x_hat)
        
        gradients = self._calc_grad(d_x_hat, x_hat, scaler)

        gradients = gradients.reshape(gradients.size(0), -1)
        penalty = (gradients.norm(2, dim=1) - center).pow(2).mean()

        if self.backward:
            penalty.backward(retain_graph=True)

        return penalty

    def dragan_gradient_penalty(self, real, D, scaler=None):
        '''DRAGAN gradient penalty

        args:
            real: torch.Tensor
                batched tensor of real images
            D: torch.nn.Module
                discriminator to calculate the gradient for
            scaler: torch.cuda.amp.GradScaler (default: None)
                gradient scaler for torch.cuda.amp
        '''

        device = real.device

        alpha = torch.rand((real.size(0), 1, 1, 1), device=device).expand(real.size())
        beta = torch.rand(real.size(), device=device)
        x_hat = real * alpha + (1 - alpha) * (real + 0.5 * real.std() * beta)
        x_hat = Variable(x_hat, requires_grad=True)

        d_x_hat = D(x_hat)

        gradients = self._calc_grad(d_x_hat, x_hat, scaler)

        gradients = gradients.reshape(gradients.size(0), -1)
        penalty = (gradients.norm(2, dim=1) - center).pow(2).mean()

        if self.backward:
            penalty.backward(retain_graph=True)    

        return penalty

    def r1_regularizer(self, real, D, scaler=None):
        '''R1 regularizer

        args:
            real: torch.Tensor
                batched tensor of real images
            D: torch.nn.Module
                discriminator to calculate the gradient for
            scaler: torch.cuda.amp.GradScaler (default: None)
                gradient scaler for torch.cuda.amp
        '''
        real_loc = Variable(real, requires_grad=True)
        d_real_loc = D(real_loc)

        gradients = self._calc_grad(d_real_loc, real_loc, scaler)

        gradients = gradients.reshape(gradients.size(0), -1)
        penalty = gradients.norm(2, dim=1).pow(2).mean() / 2.

        if self.backward:
            penalty.backward(retain_graph=True)

        return penalty

    def r2_regularizer(self, fake, D, scaler=None):
        return self.r1_regularizer(fake, D, scaler)

'''VGG'''

class VGG(nn.Module):
    '''VGG with only feature layers'''
    def __init__(self, layers=16, pretrained=True):
        super().__init__()
        assert layers in [16, 19], 'only supports VGG16 and VGG19'
        if layers == 16:
            vgg_pretrained_features = models.vgg16(pretrained=pretrained).features
            slices = [4, 9, 16, 23, 30]
        if layers == 19:
            vgg_pretrained_features = models.vgg19(pretrained=pretrained).features
            slices = [4, 9, 18, 27, 36]
        self.slice1 = nn.Sequential()
        self.slice2 = nn.Sequential()
        self.slice3 = nn.Sequential()
        self.slice4 = nn.Sequential()
        self.slice5 = nn.Sequential()
        for x in range(slices[0]):
            self.slice1.add_module(str(x), vgg_pretrained_features[x])
        for x in range(slices[0], slices[1]):
            self.slice2.add_module(str(x), vgg_pretrained_features[x])
        for x in range(slices[1], slices[2]):
            self.slice3.add_module(str(x), vgg_pretrained_features[x])
        for x in range(slices[2], slices[3]):
            self.slice4.add_module(str(x), vgg_pretrained_features[x])
        for x in range(slices[3], slices[4]):
            self.slice5.add_module(str(x), vgg_pretrained_features[x])
        for param in self.parameters():
            param.requires_grad = False

    def forward(self, X):
        h = self.slice1(X)
        h_relu1 = h
        h = self.slice2(h)
        h_relu2 = h
        h = self.slice3(h)
        h_relu3 = h
        h = self.slice4(h)
        h_relu4 = h
        h = self.slice5(h)
        h_relu5 = h
        return h_relu1, h_relu2, h_relu3, h_relu4, h_relu5

def gram_matrix(x):
    B, C, H, W = x.size()
    feat = x.reshape(B, C, H*W)
    G = torch.bmm(feat, feat.permute(0, 2, 1))
    return G.div(C*H*W)

class VGGLoss(Loss):
    '''loss using vgg'''
    def __init__(self, device, vgg=16, p=2, normalized=True, backward=False, return_all=False):
        super().__init__(backward, return_all)
        assert p in [1, 2]
        self.p = p
        self.normalized = normalized
        self.vgg = VGG(vgg, pretrained=True)
        self.vgg.to(device)

    def _check_index(self, index):
        def assert_index(index):
            assert 0 <= index <= 4
        if isinstance(index, int):
            assert_index(index)
        if isinstance(index, (list, tuple)):
            for i in index:
                assert_index(i)
    
    def loss_fn(self, x, y, p=None):
        p_ = self.p
        if p is not None:
            p_ = p
        
        if p_ == 1:
            return F.l1_loss(x, y)
        elif p_ == 2:
            return F.mse_loss(x, y)

    def normalize(self, x):
        '''normalize input tensor'''
        return TF.normalize(x, 0.5, 0.5)
    
    def style_loss(self, real, fake, block_indices=[0, 1, 2, 3], p=None):
        '''style loss introduced in
        "Perceptual Losses for Real-Time Style Transfer and Super-Resolution",
        Justin Johnson, Alexandre Alahi, and Li Fei-Fei
        '''
        self._check_index(block_indices)
        if not self.normalized:
            real, fake = self.normalize(real), self.normalize(fake)
        loss = 0
        real_acts = self.vgg(real)
        fake_acts = self.vgg(fake)
        for index in block_indices:
            loss = loss \
                + self.loss_fn(
                    gram_matrix(fake_acts[index]),
                    gram_matrix(real_acts[index]),
                    p
                )
        if self.backward:
            loss.backward(retain_graph=True)
        
        return loss
    
    def content_loss(self, real, fake, block_index=2, p=None):
        '''content loss intruduced in
        "Perceptual Losses for Real-Time Style Transfer and Super-Resolution",
        Justin Johnson, Alexandre Alahi, and Li Fei-Fei
        '''
        self._check_index(block_index)
        if not self.normalized:
            real, fake = self.normalize(real), self.normalize(fake)
        loss = 0
        real_acts = self.vgg(real)
        fake_acts = self.vgg(fake)

        loss = self.loss_fn(
            fake_acts[block_index],
            real_acts[block_index],
            p
        )

        if self.backward:
            loss.backward(retain_graph=True)
        
        return loss

    def vgg_loss(self, real, fake, block_indices=[0, 1, 2, 3, 4], p=None):
        '''perceptual loss used in pix2pixHD.
        They seem to use the activations of all convolution blocks,
        and calculates the distance with L1,
        different from using only 4 blocks and L2 in style loss and content loss.
        '''
        self._check_index(block_indices)
        if not self.normalized:
            real, fake = self.normalize(real), self.normalize(fake)
        loss = 0
        real_acts = self.vgg(real)
        fake_acts = self.vgg(fake)

        for index in block_indices:
            loss = loss + self.loss_fn(
                real_acts[index], fake_acts[index], p
            )
        
        if self.backward:
            loss.backward(retain_graph=True)
        
        return loss