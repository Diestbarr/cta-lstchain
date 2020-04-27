import pytest
import pandas as pd
import os
from lstchain.tests.test_lstchain import test_dir, mc_gamma_testfile
from lstchain.io.io import dl1_params_src_dep_lstcam_key
import subprocess as sp

output_dir = os.path.join(test_dir, 'scripts')
dl1_file = os.path.join(output_dir, 'dl1_gamma_test_large.simtel.h5')
dl2_file = os.path.join(output_dir, 'dl2_gamma_test_large.simtel.h5')
file_model_energy = os.path.join(output_dir, 'reg_energy.sav')
file_model_disp = os.path.join(output_dir, 'reg_disp_vector.sav')
file_model_gh_sep = os.path.join(output_dir, 'cls_gh.sav')


def run_program(*args):
    result = sp.run(
        args,
        stdout=sp.PIPE, stderr=sp.STDOUT, encoding='utf-8'
    )

    if result.returncode != 0:
        raise ValueError(
            f'Running {args[0]} failed with return code {result.returncode}'
            f', output: \n {result.stdout}'
        )


def test_lstchain_mc_r0_to_dl1():
    input_file = mc_gamma_testfile
    run_program(
        'lstchain_mc_r0_to_dl1',
        '-f', input_file,
        '-o', output_dir
    )
    assert os.path.exists(dl1_file)


@pytest.mark.run(after='test_lstchain_mc_r0_to_dl1')
def test_add_source_dependent_parameters():
    run_program('lstchain_add_source_dependent_parameters', '-f', dl1_file)
    dl1_params_src_dep = pd.read_hdf(dl1_file, key=dl1_params_src_dep_lstcam_key)
    assert 'alpha' in dl1_params_src_dep.columns


@pytest.mark.run(after='test_lstchain_mc_r0_to_dl1')
def test_lstchain_trainpipe():
    gamma_file = dl1_file
    proton_file = dl1_file

    run_program(
        'lstchain_mc_trainpipe',
        '-fg', gamma_file,
        '-fp', proton_file,
        '-o', output_dir
    )

    assert os.path.exists(file_model_gh_sep)
    assert os.path.exists(file_model_disp)
    assert os.path.exists(file_model_energy)


@pytest.mark.run(after='test_lstchain_trainpipe')
def test_lstchain_dl1_to_dl2():
    run_program(
        'lstchain_dl1_to_dl2',
        '-f', dl1_file,
        '-p', output_dir,
        '-o', output_dir,
    )
    assert os.path.exists(dl2_file)


@pytest.mark.run(after='test_lstchain_mc_r0_to_dl1')
def test_mc_dl1ab():
    output_file = os.path.join(output_dir, 'dl1ab.h5')
    run_program('lstchain_mc_dl1ab', dl1_file, output_file)
    assert os.path.exists(output_file)


@pytest.mark.run(after='test_lstchain_dl1_to_dl2')
def test_mc_r0_to_dl2():
    os.remove(dl1_file)
    os.remove(dl2_file)

    run_program(
        'lstchain_mc_r0_to_dl2',
        '-f', mc_gamma_testfile,
        '-p', output_dir,
        '-s1', 'False',
        '-o', output_dir,
    )
    assert os.path.exists(dl2_file)
