# Human vs Human Dataset

This dataset contains sample annotation files derived and renamed from the
[CalMS21 dataset](https://arxiv.org/abs/2104.02710) (curated data split).

Both annotation files in each recording were produced by **human annotators**,
making this a human vs human inter-annotator agreement dataset.

## Structure

```
data/dataset_human_vs_human/
  Recording_1/
    humanAnnotation_1.csv   # human annotator 1 (ground truth)
    humanAnnotation_2.csv   # human annotator 2 (predicted/compared)
  Recording_2/ ... Recording_10/
```

Each CSV has one column per behavior (binary 0/1, one row per frame).

## Dataset note

This dataset is derived from the **CalMS21 curated data** and reflects
**human vs human** annotation comparison (inter-annotator agreement).

A **human vs machine** tutorial (CalMS21 Task 1 baseline model vs human annotator)
is now available in [`demo/tutorial_calms21_task1.ipynb`](../../demo/tutorial_calms21_task1.ipynb).

## Citation

If you use this dataset please cite the original CalMS21 work:

```bibtex
@article{sun2021multi,
  title={The multi-agent behavior dataset: Mouse dyadic social interactions},
  author={Sun, Jennifer J and Karigo, Tomomi and Chakraborty, Dipam and Mohanty,
          Sharada P and Wild, Benjamin and Sun, Quan and Chen, Chen and
          Anderson, David J and Perona, Pietro and Yue, Yisong and others},
  journal={arXiv preprint arXiv:2104.02710},
  year={2021}
}
```
