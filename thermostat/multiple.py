from multiprocessing import Pool
import warnings


warnings.simplefilter('module', Warning)


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

    pool = Pool()
    results = pool.imap(_calc_epa_func, thermostats_list)
    pool.close()
    pool.join()

    metrics_dict = {}
    for output in results:
        if len(output) > 0:
            thermostat_id = output[0]['ct_identifier']
            metrics_dict[thermostat_id] = output

    # Get the order of the thermostats from the original input so the output
    # matches the order that was sent in
    metrics = []
    for thermostat in thermostats_list:
        for metric in metrics_dict.get(thermostat.thermostat_id, []):
            metrics.append(metric)
        # Prevent duplicate thermostat IDs from being double-counted
        metrics_dict.pop(thermostat.thermostat_id, None)

    return metrics
