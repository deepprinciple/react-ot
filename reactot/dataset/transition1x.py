import copy
import numpy as np
import torch

from reactot.dataset.base_dataset import BaseDataset, ATOM_MAPPING, SAM_CHARGED_ATOM_MAPPING


FRAG_MAPPING = {
    "reactant": "product",
    "transition_state": "transition_state",
    "product": "reactant",
}


def reflect_z(x):
    x = np.array(x)
    x[:, -1] = - x[:, -1]
    return x


class ProcessedTS1x(BaseDataset):
    def __init__(
        self,
        npz_path,
        center=True,
        pad_fragments=0,
        device="cuda",
        zero_charge=False,
        remove_h=False,
        single_frag_only=True,
        multi_frag_only=False,
        swapping_react_prod=False,
        append_frag=False,
        reflection=False,
        use_by_ind=False,
        only_ts=False,
        only_rp=False,
        confidence_model=False,
        position_key="positions",
        ediff=None,
        ts_guess=False,
        react_type=None,
        atom_mapping=ATOM_MAPPING,
        **kwargs,
    ):
        super().__init__(
            npz_path=npz_path,
            center=center,
            device=device,
            zero_charge=zero_charge,
            remove_h=remove_h,
            atom_mapping=atom_mapping,
        )
        if confidence_model:
            use_by_ind = False
        if remove_h:
            print("remove_h is ignored because it is not reasonble for TS.")
        if single_frag_only:
            print("Filtering: Maintain only uni-molecular reactions")
            single_frag_inds = np.where(
                np.array(self.raw_dataset["single_fragment"]) == 1)[0]
        elif multi_frag_only:
            print("Filtering: Maintain only multi-molecular reactions")
            single_frag_inds = np.where(
                np.array(self.raw_dataset["single_fragment"]) == 0)[0]
        else:
            single_frag_inds = np.array(range(len(self.raw_dataset["single_fragment"])))
        if use_by_ind:
            print("Filtering: Maintain based on data partitioning")
            use_inds = self.raw_dataset["use_ind"]
        else:
            use_inds = range(len(self.raw_dataset["single_fragment"]))
        if react_type is not None:
            print(f"Filtering: Maintain reactions only with type {react_type}")
            intended_inds = np.where(
                np.array(self.raw_dataset["type"]) == react_type)[0]
        else:
            intended_inds = range(len(self.raw_dataset["single_fragment"]))
        single_frag_inds = list(
            set(single_frag_inds).intersection(
                set(use_inds)).intersection(
                set(intended_inds))
        )
        print(f"position key: {position_key}, # of data: {len(single_frag_inds)}")

        data_duplicated = copy.deepcopy(self.raw_dataset)
        for k, mapped_k in FRAG_MAPPING.items():
            for v, val in data_duplicated[k].items():
                self.raw_dataset[k][v] = [val[ii] for ii in single_frag_inds]
                if swapping_react_prod:
                    mapped_val = data_duplicated[mapped_k][v]
                    self.raw_dataset[k][v] += [mapped_val[ii] for ii in single_frag_inds]
        if reflection:
            for k, mapped_k in FRAG_MAPPING.items():
                for v, val in self.raw_dataset[k].items():
                    if v in ["wB97x_6-31G(d).forces", position_key]:
                        self.raw_dataset[k][v] += [
                            reflect_z(_val) for _val in val]
                    else:
                        self.raw_dataset[k][v] += val

        self.reactant = self.raw_dataset["reactant"]
        self.transition_state = self.raw_dataset["transition_state"]
        self.product = self.raw_dataset["product"]

        self.n_fragments = pad_fragments + 3
        self.device = torch.device(device)
        n_samples = len(self.reactant["charges"])
        self.n_samples = len(self.reactant["charges"])

        self.data = {}
        repeat = 2 if swapping_react_prod else 1
        if confidence_model:
            self.data["target"] = torch.tensor(self.raw_dataset["target"] * repeat).unsqueeze(1)
            self.data["rmsd"] = torch.tensor(self.raw_dataset["rmsd"] * repeat).unsqueeze(1)
        if ediff is not None:
            self.data["ediff"] = torch.tensor(self.raw_dataset[ediff]["ediff"] * repeat).unsqueeze(1)
        if ts_guess:
            self.data["ts_guess"] = [torch.tensor(self.raw_dataset[ts_guess][ii]) for ii in single_frag_inds] * repeat
        if not only_ts:
            if not only_rp:
                if not append_frag:
                    self.process_molecules("reactant", n_samples, idx=0, position_key=position_key)
                    self.process_molecules("transition_state", n_samples, idx=1)
                    self.process_molecules("product", n_samples, idx=2, position_key=position_key)
                else:
                    self.process_molecules("reactant", n_samples, idx=0, append_charge=0, position_key=position_key)
                    self.process_molecules("transition_state", n_samples, idx=1, append_charge=1)
                    self.process_molecules("product", n_samples, idx=2, append_charge=0, position_key=position_key)

                for idx in range(pad_fragments):
                    self.patch_dummy_molecules(idx + 3)
            else:
                self.process_molecules("reactant", n_samples, idx=0, position_key=position_key)
                self.process_molecules("product", n_samples, idx=1, position_key=position_key)
        else:
            if not append_frag:
                self.process_molecules("transition_state", n_samples, idx=0)
            else:
                self.process_molecules("transition_state", n_samples, idx=0, append_charge=1)
            # for idx in range(2):
            #     self.patch_dummy_molecules(idx + 1)
            
        # if "charge" in self.raw_dataset:
        if False:
            charge_duplicated = copy.deepcopy(self.raw_dataset["charge"])
            self.data["condition"] = [
                torch.tensor([charge_duplicated[ii]], dtype=torch.int64, device=self.device,).reshape(1, 1) 
                for ii in single_frag_inds
            ]
            if swapping_react_prod:
                self.data["condition"] += self.data["condition"]
            assert len(self.data["condition"]) == self.n_samples
        else:
            self.data["condition"] = [
                torch.zeros(size=(1, 1), dtype=torch.int64, device=self.device,)
                for _ in range(self.n_samples)
            ]
