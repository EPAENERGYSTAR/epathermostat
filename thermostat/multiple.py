from multiprocessing import Pool

from thermostat.run_summary import NO_QUALIFYING_CORE_DAYS


def _calc_epa_func(thermostat):
    """ Takes an individual thermostat and runs the
    calculate_epa_field_savings_metrics method. This method is necessary for
    the multiprocessing pool as map / imap need a function to run on.

    Parameters
    ----------
    thermostat : thermostat

    Returns
    -------
    results : results from running calculate_epa_field_savings_metrics
    """
    results = thermostat.calculate_epa_field_savings_metrics()
    return results


def multiple_thermostat_calculate_epa_field_savings_metrics(thermostats):
    """ Takes a list of thermostats and uses Python's Multiprocessing module to
    run as many processes in parallel as the system will allow.

    Parameters
    ----------
    thermostats : thermostats iterator
        A list of the thermostats run the calculate_epa_field_savings_metrics
        upon. When this is the ImportedThermostats returned by
        :func:`thermostat.importers.from_csv`, thermostats that qualify for
        no core days are recorded in its ``.summary`` -- otherwise that loss
        is invisible, since such a thermostat imports cleanly and simply
        contributes no rows.

    Returns
    -------
    metrics : list
        Returns a list of the metrics calculated for the thermostats
    """
    # Read the summary off the iterator before consuming it.
    summary = getattr(thermostats, "summary", None)

    # Convert the thermostats iterator to a list
    thermostats_list = list(thermostats)

    # Pool.map preserves input order, so the results already match the order
    # they were sent in. The previous code used imap and then rebuilt the
    # order by hand from a dict keyed on thermostat_id, which silently dropped
    # the second of any two thermostats sharing an id.
    with Pool() as pool:
        results = pool.map(_calc_epa_func, thermostats_list)

    metrics = []
    for thermostat, output in zip(thermostats_list, results):
        # a thermostat with no qualifying core day sets yields no metrics;
        # skip it rather than indexing an empty result (which would raise)
        if not output:
            if summary is not None:
                summary.record(
                    thermostat_id=thermostat.thermostat_id,
                    zipcode=thermostat.zipcode,
                    station=thermostat.station,
                    stage="metrics",
                    reason=NO_QUALIFYING_CORE_DAYS,
                    detail="imported, but qualified for no core heating or "
                           "cooling days")
            continue
        metrics.extend(output)

    return metrics
