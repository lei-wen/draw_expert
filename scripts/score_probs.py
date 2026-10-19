#!/usr/bin/env python3
"""Compute shared-component bivariate Poisson probabilities; does not fit parameters."""
import argparse
import json
import math


def poisson(rate, n):
    values = [math.exp(-rate)]
    for i in range(1, n + 1):
        values.append(values[-1] * rate / i)
    return values


def calculate(mu, lam, kappa=0.0, odds=None):
    if not all(math.isfinite(v) for v in (mu, lam, kappa)):
        raise ValueError('Parameters must be finite')
    if not (0 <= mu <= 30 and 0 <= lam <= 30 and 0 <= kappa <= min(mu, lam)):
        raise ValueError('Require 0<=mu,lam<=30 and 0<=kappa<=min(mu,lam)')
    if odds is not None and (len(odds) != 3 or any(not math.isfinite(v) or v <= 1 for v in odds)):
        raise ValueError('Provide three finite decimal odds >1: home draw away')
    n = 10
    while True:
        px, py = poisson(mu, n), poisson(lam, n)
        if max(0., 1-sum(px)) + max(0., 1-sum(py)) < 1e-9:
            break
        n += 10
    pa, pb, pc = poisson(mu-kappa, n), poisson(lam-kappa, n), poisson(kappa, n)
    cells = []
    totals = {'home': 0.0, 'draw': 0.0, 'away': 0.0}
    for x in range(n+1):
        for y in range(n+1):
            p = math.fsum(pa[x-k]*pb[y-k]*pc[k] for k in range(min(x, y)+1))
            totals['home' if x>y else 'draw' if x==y else 'away'] += p
            cells.append((p, x, y))
    ranked = sorted(cells, key=lambda item: (-item[0], item[1], item[2]))
    def rows(items):
        return [{'score': f'{x}:{y}', 'probability': p} for p, x, y in items[:3]]
    result = {'parameters': {'mu': mu, 'lambda': lam, 'kappa': kappa},
              'model': 'independent' if kappa==0 else 'shared_component_bivariate_poisson',
              'probabilities': totals, 'omitted_mass': max(0., 1-math.fsum(totals.values())),
              'max_score': n, 'top_scores': rows(ranked),
              'top_draw_scores': rows([v for v in ranked if v[1]==v[2]])}
    if odds is not None:
        inv = [1/o for o in odds]
        market = dict(zip(('home','draw','away'), [v/sum(inv) for v in inv]))
        result['market_proportional_devig'] = market
        result['draw_gap_percentage_points'] = 100*(totals['draw']-market['draw'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mu', type=float, required=True)
    parser.add_argument('--lam', type=float, required=True)
    parser.add_argument('--kappa', type=float, default=0.)
    parser.add_argument('--odds', type=float, nargs=3, metavar=('HOME','DRAW','AWAY'))
    args = parser.parse_args()
    try:
        result = calculate(args.mu, args.lam, args.kappa, args.odds)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
