from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from fastai.tabular.all import *
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_categorical_dtype
from fastbook import *
import fastbook
import sys
import aidata
import logging
import logging.config

logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)
logger = logging.getLogger("fastai")

pd.options.display.max_rows = 100
pd.options.display.max_columns = 8000
pd.options.display.max_colwidth = 1000
pd.options.display.width = 10000


def match_cols(r1, r2, cols):
    # print(f"matching {r1}, {r2}")
    for col in cols:
        if r1[col] != r2[col]:
            # print(f"bad {col}: {r1[col]} != {r2[col]}")
            return False
    # print(f"GOOD")

    return True


def get_to(csv_path=None):
    if not csv_path:
        print("loading to.pkl", file=sys.stderr, flush=True)
        to = load_pickle("to.pkl")
        logger.debug(f"TO: {to[:2]}")
    else:
        logger.debug("READING csv...")
        if os.path.exists('m.pkl'):
            os.remove("m.pkl")
        df = pd.read_csv(csv_path)
        logger.debug(f"df:\n {df[:100]}")

        # df = df.drop(["MONSTER_VULNERABLE"], axis=1)
        # df = df[df.MONSTER_HP <= 8]
        # df = df.reset_index(drop=True)

        logger.debug(f"df.describe:\n {df.describe()}")
        last_game = df.max(0)['GAME']
        logger.debug(f"last_game:\n {last_game}")

        trn_split = df.index[df['GAME'] < last_game*.8].tolist()
        val_split = df.index[df['GAME'] >= last_game*.8].tolist()

        df['FINAL_HP_NEGATIVE'] = -df['FINAL_HP']
        logger.debug(f"df:\n {df[:100]}")

        cat_names = ['PLAY']
        cont_names = aidata.CONT_DATA.split(',')
        dep_var = 'FINAL_HP_DELTA'
        dep_var = 'FINAL_HP_NEGATIVE'
        to = TabularPandas(df,
                           procs=[Categorify],
                           cat_names=cat_names,
                           cont_names=cont_names,
                           y_names=dep_var,
                           splits=(trn_split, val_split))
        save_pickle('to.pkl', to)
        logger.debug(f"TO: {to[:10]}")

    return to


def r_mse(pred, y):
    return round(math.sqrt(((pred-y)**2).mean()), 6)


def m_rmse(m, xs, y):
    return r_mse(m.predict(xs), y)


def rf(xs, y, n_estimators=40, max_samples=200_000,
       max_features=0.5, min_samples_leaf=5, **kwargs):
    return RandomForestRegressor(n_jobs=-1, n_estimators=n_estimators,
                                 max_samples=max_samples, max_features=max_features,
                                 min_samples_leaf=min_samples_leaf, oob_score=True).fit(xs, y)


def get_m_randomforest(xs, y):
    logger.debug(f"xs: {xs[:10]}, y: {y[0]}")
    if os.path.exists("m.pkl"):
        print("loading m.pkl", file=sys.stderr, flush=True)
        m = load_pickle("m.pkl")
    else:
        print("learning...", file=sys.stderr, flush=True)
        m = rf(xs, y, max_samples=0.8)
        save_pickle('m.pkl', m)
        logger.debug(f"PREDICT: {m.predict(xs[10:12]),xs[10:12]}")
    return m


def get_m_decision(xs, y):
    logger.debug(f"xs: {xs[:10]}, y: {y[0]}")
    if os.path.exists("m.pkl"):
        logger.debug("loading m.pkl...")
        m = load_pickle("m.pkl")
    else:
        print("learning...", file=sys.stderr, flush=True)
        best_val_err = 100000
        mln = 1
        while True:
            m = DecisionTreeRegressor(
                max_leaf_nodes=mln*2
            ).fit(xs, y)
            err, val_err = m_rmse(m, xs, y), m_rmse(m, valid_xs, valid_y)
            logger.debug(f"errs: {err}, {val_err}, {mln}")

            if val_err >= best_val_err or mln > 40960:
                break
            best_val_err = val_err
            mln *= 2
        print(f"nodes: {mln}", file=sys.stderr, flush=True)

        m = DecisionTreeRegressor(
            max_leaf_nodes=mln
        ).fit(xs, y)
        err, val_err = m_rmse(m, xs, y), m_rmse(m, valid_xs, valid_y)
        logger.debug(f"final errs: {err}, {val_err}, {mln}")
        print(f"errs: {err}, {val_err}, {mln}", file=sys.stderr)

        save_pickle('m.pkl', m)
        # logger.debug(f"PREDICT: {m.predict(xs[10:12]),xs[10:12]}")
    return m


get_m = get_m_randomforest
# get_m = get_m_decision
to = None
m = None


def setup_model():
    global to, m
    fastbook.setup_book()
    to = get_to()
    xs, y = to.train.xs, to.train.y
    return get_m(xs, y)


def predict(data, m):
    cats = to.procs.categorify.classes['PLAY']

    # data["PLAY"] = [cats.o2i[x.name] for x in data["PLAY"]]
    data["PLAY"] = [cats.o2i[x] for x in data["PLAY"]]
    test_data = pd.DataFrame(data)
    logger.debug(f"data: \n{test_data}")
    p = m.predict(test_data)
    # print(f"{data} -> {p}")
    return p


def rf_feat_importance(m, df):
    return pd.DataFrame({'cols': df.columns, 'imp': m.feature_importances_}
                        ).sort_values('imp', ascending=False)


if __name__ == "__main__":
    fastbook.setup_book()

    to = get_to(sys.argv[1] if len(sys.argv) else None)
    xs, y = to.train.xs, to.train.y
    valid_xs, valid_y = to.valid.xs, to.valid.y

    m = get_m(xs, y)
    fi = rf_feat_importance(m, xs)
    print(f"feature importance:\n{fi}", file=sys.stderr, flush=True)
    logger.debug(f"fi: {fi}")

    if len(sys.argv):
        sys.exit(0)
    print(
        f"ERRORS: training {m_rmse(m, xs, y)}, validation {m_rmse(m, valid_xs, valid_y)}")
    logger.debug(
        f"to: {to[:2]}\nclasses: {to.procs.categorify.classes['PLAY']}")
    cats = to.procs.categorify.classes['PLAY']
    test = pd.DataFrame(
        {
            #         "PLAY": [3],
            "PLAY": [cats.o2i[x] for x in ("DEFEND", "DEFEND", "STRIKE", "BASH")],
            "ENERGY": [3] * 4,
            "PLAYER_HP": [72] * 3,
            "PLAYER_BLOCK": [0, 12, 0, 0],
            "MONSTER_HP": [8] * 4,
            "MONSTER_ATTACK": [12] * 4,
            "MONSTER_BLOCK": [0] * 4,
            "MONSTER_VULNERABLE": [0] * 4,
        }
    )

    logger.debug(f"test: {test}\n\n{m.predict(test)}")
