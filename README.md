# React-OT: Optimal Transport for Generating Transition State in Chemical Reactions

In this work, we developed React-OT, an optimal transport approach to generate TSs of an elementary reaction in a fully deterministic manner. It is based on our previously developed diffusion-based generative model for generating 3D chemical reactions, [OA-ReactDiff](https://github.com/chenruduan/OAReactDiff). React-OT has been improved for generating transition state (TS) structures for a given reactants and products (double-ended search problem), enabling it to generate highly accurate transition state structures while maintaining an extremely high inference speed.

![image](https://github.com/deepprinciple/react-ot/blob/main/reactot/Figures/figure1.jpg)
Fig. 1 | Overview of the diffusion model and optimal transport framework for generating TS. a. Learning the joint distribution of structures in elementary reactions (reactant in red, TS in yellow, and product in blue). b. Stochastic inference with inpainting in OA-ReactDiff. c. Deterministic inference with React-OT.

We trained React-OT on Transition1x, a dataset that contains paired reactants, TSs, and products calculated from climbing-image NEB obtained with DFT (ωB97x/6-31G(d)). In React-OT, the object-aware version of LEFTNet is used as the scoring network to fit the transition kernel (see [LEFTNet](https://arxiv.org/abs/2304.04757)). React-OT achieves a mean RMSD of 0.103 Å between generated and true TS structures on the set-aside test reactions of Transition1x, significantly improved upon previous state-of-the-art TS prediction methods.

![image](https://github.com/deepprinciple/react-ot/blob/main/reactot/Figures/figure2.jpg)
Fig. 2 | Structural and energetic performance of diffusion and optimal transport generated TS structures. a. Cumulative probability for structure root mean square deviation (RMSD) (left) and absolute energy error (|∆E TS|) (right) between the true and generated TS on 1,073 set-aside test reactions.  b. Reference TS structure, OA-ReactDiff TS sample (red), and React-OT structure (orange) for select reactions. c. Histogram (gray, left y axis) and cumulative probability(blue, right y axis) showing the difference of RMSD (left) and |∆ETS|(right) between OA-ReactDiff recommended and React-OT structures compared to reference TS. d. Inference time in seconds for single-shot OA-ReactDiff, 40-shot OA-ReactDiff with recommender, and React-OT.

We envision that the remarkable accuracy and rapid inference of React-OT will be highly useful when integrated with the current high-throughput TS search workflow. This integration will facilitate the exploration of chemical reactions with unknown mechanisms.

## Environment set-up
```
conda env create -f env.yaml
conda activate reactot && pip install -e .
```

## Download data
The processed data is uploaded on zenodo, [download link](https://zenodo.org/records/13131875). You need to put both pickle files under the data directory.

```
mkdir reactot/data
mkdir reactot/data/transition1x
mv PATH_TO_PKL_FILES reactot/data/transition1x/
```

## Evaluation using a pre-trained model
The pre-trained model can be downloaded through the [download link](https://zenodo.org/records/13131875).
```
python evaluation.py --checkpoint PATH_TO_CHECKPOINT --solver ode --nfe 10
``` 

## Training
```
python -m reactot.trainer.train_rpsb_ts1x
```
Note that the default parameters and model types are used in the current command. More detailed instructions on model training will be updated soon.

## Data used in this work
1. [Transition1x](https://gitlab.com/matschreiner/Transition1x)
2. [RGD1](https://figshare.com/articles/dataset/model_reaction_database/21066901)
3. [Berkholz-15](https://onlinelibrary.wiley.com/doi/abs/10.1002/jcc.23910)

---
## About Deep Principle
This project is part of the open-source work at [Deep Principle](https://www.deepprinciple.com), an AI for Materials company advancing scientific discovery.
[Mira — AI Scientist Platform](https://agentmira.io) is built by Deep Principle for scientific research and R&D workflows.
