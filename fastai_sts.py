from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from fastai.tabular.all import *
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_categorical_dtype
from fastbook import *
import fastbook


def match_cols(r1, r2, cols):
    print(f"matching {r1}, {r2}")
    for col in cols:
        if r1[col] != r2[col]:
            print(f"bad {col}: {r1[col]} != {r2[col]}")
            return False
    print(f"GOOD")

    return True


def get_to():
    if os.path.exists('to.pkl'):
        print("loading to.pkl...")
        to = load_pickle('to.pkl')
        print(f"TO: {to[:2]}")
    else:
        print("READING csv...")
        if os.path.exists('m.pkl'):
            os.remove("m.pkl")
        df = pd.read_csv(
            '/mnt/c/Users/steph/Documents/slaythespire/sts.save.csv')
        trn_split = df.index[df['GAME'] < df.max(0)['GAME']*.8].tolist()
        val_split = df.index[df['GAME'] >= df.max(0)['GAME']*.8].tolist()
        splits = trn_split, val_split

        df2 = df.drop([
            # 'GAME',
            # 'N_TURN',
            #     'PLAY'
        ], axis=1)
        df2['BEST_FINAL_HP'] = df2.groupby(
            ['PLAYER_HP', 'MONSTER_BLOCK', 'MONSTER_HP', 'MONSTER_ATTACK'])['FINAL_HP'].transform('max')

        df_joined = df2
        df_joined['FINAL_HP_DELTA'] = df_joined["BEST_FINAL_HP"] - \
            df_joined["FINAL_HP"]
        cat_names = ['PLAY']
        cont_names = [
            #     'N_PLAY',
            'ENERGY', 'PLAYER_HP', 'MONSTER_HP', 'MONSTER_ATTACK', 'MONSTER_BLOCK', 'ATTACK', 'VULNERABLE', 'DEFEND']
        dep_var = 'FINAL_HP_DELTA'
        dfj = df_joined.drop(
            ['N_PLAY', 'PLAY', 'GAME', 'N_TURN', 'BEST_FINAL_HP', 'FINAL_HP'], axis=1)
        to = TabularPandas(dfj,
                           #                    procs=[Categorify],
                           #                    ,FillMissing,Normalize],
                           #                    cat_names = cat_names,
                           cont_names=cont_names,
                           y_names=dep_var,
                           splits=splits)
        save_pickle('to.pkl', to)
    return to


def r_mse(pred, y):
    return round(math.sqrt(((pred-y)**2).mean()), 6)


def m_rmse(m, xs, y):
    return r_mse(m.predict(xs), y)


def get_m(xs, y):
    print(f"xs: {xs[:10]}, y: {y[0]}")
    if os.path.exists("m.pkl"):
        print("loading m.pkl...")
        m = load_pickle("m.pkl")
    else:
        print("learning...")
        best_val_err = 100000
        mln = 1
        while True:
            m = DecisionTreeRegressor(
                max_leaf_nodes=mln*2
            ).fit(xs, y)
            err, val_err = m_rmse(m, xs, y), m_rmse(m, valid_xs, valid_y)
            print(f"errs: {err}, {val_err}, {mln}")
            if val_err > best_val_err:
                break
            best_val_err = val_err
            mln *= 2

        m = DecisionTreeRegressor(
            max_leaf_nodes=mln
        ).fit(xs, y)
        save_pickle('m.pkl', m)
    return m


to = None
m = None


def setup_model():
    global to, m
    fastbook.setup_book()
    to = get_to()
    xs, y = to.train.xs, to.train.y
    return get_m(xs, y)


def predict(data, m):
    test_data = pd.DataFrame(data)
    # print(f"{test_data}")
    p = m.predict(test_data)[0]
    # print(f"{data} -> {p}")
    return p


if __name__ == "__main__":
    fastbook.setup_book()

    to = get_to()
    xs, y = to.train.xs, to.train.y
    valid_xs, valid_y = to.valid.xs, to.valid.y

    m = get_m(xs, y)

    print(f"ERRORS {m_rmse(m, xs, y), m_rmse(m, valid_xs, valid_y)}")
    print(f"to: {to[:2]}")
    test = pd.DataFrame(
        {
            #         "PLAY": [3],
            "ENERGY": [2] * 3,
            "PLAYER_HP": [72] * 3,
            "MONSTER_HP": [8] * 3,
            "MONSTER_ATTACK": [12] * 3,
            "MONSTER_BLOCK": [0] * 3,
            "ATTACK": [0, 6, 8],
            "VULNERABLE": [0, 0, 2],
            "DEFEND": [5, 0, 0],
        }
    )

    print(f"test: {test,xs[:2],m.predict(test)}")
