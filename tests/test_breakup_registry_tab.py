from supersonic_atomizer.breakup.registry import select_breakup_model
from supersonic_atomizer.domain.case_models import ModelSelectionConfig


def test_select_breakup_model_returns_tab_instance():
    cfg = ModelSelectionConfig(breakup_model="tab")
    model = select_breakup_model(cfg)
    from supersonic_atomizer.breakup.tab import TABBreakupModel

    assert isinstance(model, TABBreakupModel)
