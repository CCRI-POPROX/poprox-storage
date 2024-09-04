from poprox_storage.concepts.experiment import Experiment, Team
from poprox_storage.concepts.manifest import manifest_to_experiment, parse_manifest_toml
from poprox_storage.paths import project_root


def test_load_manifest():
    with open(project_root() / "tests" / "data" / "sample_manifest.toml") as f:
        sample_manifest = f.read()
    manifest = parse_manifest_toml(sample_manifest)
    experiment = manifest_to_experiment(manifest)

    assert isinstance(experiment, Experiment)
    assert isinstance(experiment.owner, Team)
    assert len(experiment.groups) == 3
    assert len(experiment.recommenders) == 3
    assert len(experiment.phases) == 3
