from pathlib import Path

import pandas as pd
from loguru import logger

from hcme import config


def metric_to_csv(metric, outpath="", **kwargs):
    """Export record-format JSON to a CSV."""
    out_path = (
        Path(outpath)
        if outpath
        else config.output_dir / f"{metric.domain}/{metric.name}.csv"
    )
    out_path.parent.mkdir(exist_ok=True, parents=True)
    logger.info("Exporting data to {out_path}", out_path=out_path)
    pd.DataFrame(metric.data).to_csv(out_path, **kwargs)
