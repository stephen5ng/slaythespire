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
        print(f"df: {df[:8]}")
        trn_split = df.index[df['GAME'] < df.max(0)['GAME']*.8].tolist()
        val_split = df.index[df['GAME'] >= df.max(0)['GAME']*.8].tolist()
        df['FINAL_HP_DELTA'] = (df.groupby(
                ['PLAYER_HP', 'MONSTER_BLOCK', 'MONSTER_HP', 'MONSTER_ATTACK'])['FINAL_HP'].transform('max') - 
                                df["FINAL_HP"])

        cat_names = ['PLAY']
        cont_names = [ 'ENERGY', 'PLAYER_HP', 'MONSTER_HP', 'MONSTER_ATTACK', 'MONSTER_BLOCK']
        dep_var = 'FINAL_HP_DELTA'
        to = TabularPandas(df,
                           procs=[Categorify],
                           cat_names=cat_names,
                           cont_names=cont_names,
                           y_names=dep_var,
                           splits=(trn_split, val_split))
        save_pickle('to.pkl', to)
        print(f"TO: {to[:10]}")

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
        print(f"PREDICT: {m.predict(xs[10:12]),xs[10:12]}")
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
    cats = to.procs.categorify.classes['PLAY']
    
    data["PLAY"] = [cats.o2i[x.name] for x in data["PLAY"]]
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
    print(f"to: {to[:2]}, CCC: {to.procs.categorify.classes['PLAY']}")
    cats = to.procs.categorify.classes['PLAY']
    test = pd.DataFrame(
        {
            #         "PLAY": [3],
            "PLAY": [cats.o2i[x] for x in ("DEFEND", "STRIKE", "BASH")],
            "ENERGY": [3] * 3,
            "PLAYER_HP": [72] * 3,
            "MONSTER_HP": [4] * 3,
            "MONSTER_ATTACK": [12] * 3,
            "MONSTER_BLOCK": [0] * 3,
        }
    )

    print(f"test: {test,xs[:2],m.predict(test)}")
