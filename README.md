
<p align="center">
    <img alt="StyleGAN2 result" src="https://raw.githubusercontent.com/STomoya/animeface/master/implementations/StyleGAN2/result/118000.png">
</p>

# animeface

deep models for anime images.

## Datasets

- [anime-face-dataset](https://www.kaggle.com/splcher/animefacedataset)  
    Anime faces collected from [Getchu.com](http://www.getchu.com/).  
    Based on [Mckinsey666](https://github.com/Mckinsey666/Anime-Face-Dataset)'s dataset.  
    63.6K images.
- [Tagged Anime Illustrations](https://www.kaggle.com/mylesoneill/tagged-anime-illustrations)  
    A subset of the [Danbooru2017](https://www.gwern.net/Danbooru2017), and the [moeimouto face dataset](http://www.nurs.or.jp/~nagadomi/animeface-character-dataset/).  
    337K Danbooru images, 17.4K moeimouto face images.
- [Danbooru2019 Portraits](https://www.gwern.net/Crops#danbooru2019-portraits) [1]  
    Portraits of anime characters collected from [Danbooru2019](https://www.gwern.net/Danbooru2019).  
    302K portraits.

## Models

"code" is indicated when only an official implementation exists.

### Generative Adversarial Networks (GANs)

- auxiliary classifier GAN (ACGAN).  1610
    [paper](https://arxiv.org/abs/1610.09585)
- big GAN (BigGAN).  1809
    [paper](https://arxiv.org/abs/1809.11096) | [code](https://github.com/ajbrock/BigGAN-PyTorch)
- conditional GAN (cGAN).  1411
    [paper](https://arxiv.org/abs/1411.1784)
- deep convolutional GAN (DCGAN).  1511
    [paper](https://arxiv.org/abs/1511.06434)
- deep regret analytic GAN (DRAGAN).  1705
    [paper](https://arxiv.org/abs/1705.07215) | [code](https://github.com/kodalinaveen3/DRAGAN)
- generative adversarial networks (GAN).  1406
    [paper](https://arxiv.org/abs/1406.2661)
- Image-to-image Translation via Hierarchical Style Disentanglement (HiSD)  2103
    [paper](https://arxiv.org/abs/2103.01456) | [code](https://github.com/imlixinyang/HiSD)
- Hologram(?) GAN (HoloGAN).  1904
    [paper](https://arxiv.org/abs/1904.01326) | [code](https://github.com/thunguyenphuoc/HoloGAN)
- progressive growing of GANs (PGGAN). 1710 
    [paper](https://arxiv.org/abs/1710.10196) | [code](https://github.com/tkarras/progressive_growing_of_gans)
- pix2ix.  1703
    [paper](https://arxiv.org/abs/1703.10593) | [code](https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix)
- pix2pix HD.  1711
    [paper](https://arxiv.org/abs/1711.11585) | [code](https://github.com/NVIDIA/pix2pixHD)
- single GAN (SinGAN).  1905
    [paper](https://arxiv.org/abs/1905.01164) | [code](https://github.com/tamarott/SinGAN)
- Spatially-Adaptive Normalization (SPADE).  1903
    [paper](https://arxiv.org/abs/1903.07291) | [code](https://github.com/NVlabs/SPADE)
- style-based GAN (StyleGAN).  1812
    [paper](https://arxiv.org/abs/1812.04948) | [code](https://github.com/NVlabs/stylegan)
- style-based GAN 2 (StyleGAN2).  1912
    [paper](https://arxiv.org/abs/1912.04958) | [code](https://github.com/NVlabs/stylegan2)
- Transformer-based GAN (TransGAN).  2102
    [paper](https://arxiv.org/abs/2102.07074) | [code](https://github.com/VITA-Group/TransGAN)
- unsupervised GAN with adaptive layer-instance normalization (UGATIT).  1907
    [paper](https://arxiv.org/abs/1907.10830) | [code](https://github.com/taki0112/UGATIT)
- Wasserstein GAN (WGAN).  1701
    [paper](https://arxiv.org/abs/1701.07875)
- WGAN with gradient penalty (WGAN_gp).  1704
    [paper](https://arxiv.org/abs/1704.00028)
- zero-centered gradient penalty. 1705 
    [paper](https://arxiv.org/abs/1705.09367)
- simplified zero-centered gradient penality.  1801
    [paper](https://arxiv.org/abs/1801.04406) | [code](https://github.com/LMescheder/GAN_stability)

### Auto Encoders

- Auto Encoder (AE)  
    [paper](https://www.cs.toronto.edu/~hinton/science.pdf)
- Variational Auto Encoder (VAE).  1312
    [paper](https://arxiv.org/abs/1312.6114)

### Other

- AdaBelief optimizer  
    [paper](https://arxiv.org/abs/2010.07468) | [code](https://github.com/juntang-zhuang/Adabelief-Optimizer)
- Adaptive Discriminator Augmentation (ADA).  
    [paper](https://arxiv.org/abs/2006.06676) | [code](https://github.com/NVlabs/stylegan2-ada)
- differentiable augmentation (DiffAugment).  
    [paper](https://arxiv.org/abs/2006.10738) | [code](https://github.com/mit-han-lab/data-efficient-gans)
- pixel shuffle.  
    [paper](https://arxiv.org/abs/1609.05158)

## Weights

See `weights.md`

## Reference

```
[1] Gwern Branwen, Anonymous, & The Danbooru Community;
    “Danbooru2019 Portraits: A Large-Scale Anime Head Illustration Dataset”,
    2019-03-12. Web. Accessed 2020/09/17,
    https://www.gwern.net/Crops#danbooru2019-portraits
```

## Author

[Tomoya Sawada](https://github.com/STomoya)
