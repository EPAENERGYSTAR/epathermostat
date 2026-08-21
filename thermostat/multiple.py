from multiprocessing import Pool


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
        upon.

    Returns
    -------
    metrics : list
        Returns a list of the metrics calculated for the thermostats
    """
    # Convert the thermostats iterator to a list
    thermostats_list = list(thermostats)

    # Pool.map preserves input order, so the results already match the order
    # they were sent in. The previous code used imap and then rebuilt the
    # order by hand from a dict keyed on thermostat_id, which silently dropped
    # the second of any two thermostats sharing an id.
    with Pool() as pool:
        results = pool.map(_calc_epa_func, thermostats_list)

    metrics = []
    for output in results:
        # a thermostat with no qualifying core day sets yields no metrics;
        # skip it rather than indexing an empty result (which would raise)
        if not output:
            continue
        metrics.extend(output)

    return metrics
