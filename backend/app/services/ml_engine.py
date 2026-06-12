"""ml_engine smoke-test copy — written to /tmp to bypass iCloud eviction."""
from __future__ import annotations
import warnings
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
warnings.filterwarnings("ignore")

RANDOM_STATE = 42
CV_FOLDS = 5
NESTED_OUTER_FOLDS = 3
NESTED_INNER_FOLDS = 3
N_JOBS = 1
OPPORTUNITY_TYPE_COLUMN = "Opportunity Type"
USER_COLUMN = "User"
PRICE_COLUMN = "Price"
MANUAL_ENGINEERED_FEATURES: List[str] = ["IAM, Cybersecurity or IT Department","Company Size"]
LEAKAGE_RISK_COLUMNS: List[str] = ["Status","Final Status","Outcome","Won Date","Lost Date","Close Date","Closed Date","Decision","Win Probability","Win Rate"]
LEAKAGE_KEYWORDS: List[str] = ["result"]
_AUTO_FEATURES: frozenset = frozenset({"Price_Log","Price_Per_User","Price_Per_User_Log","Offer_Year","Offer_Month","Offer_Quarter","User_Log","Has_Competition","Competition_Count","Has_Partner","Product_Opportunity_Type","Sector_Source","Project_End_Known"})

def find_column_ignore_case(columns, name: str) -> Optional[str]:
    for col in columns:
        if str(col).lower() == str(name).lower():
            return col
    return None

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    rename_map: Dict[str,str] = {}
    typo_col = find_column_ignore_case(df.columns, "Oportunity Type")
    if typo_col is not None and typo_col != OPPORTUNITY_TYPE_COLUMN:
        rename_map[typo_col] = OPPORTUNITY_TYPE_COLUMN
    quoted_price_col = find_column_ignore_case(df.columns, "Quoted Price")
    if quoted_price_col is not None and quoted_price_col != PRICE_COLUMN:
        rename_map[quoted_price_col] = PRICE_COLUMN
    hash_user_col = find_column_ignore_case(df.columns, "#user")
    if hash_user_col is not None and hash_user_col != USER_COLUMN:
        rename_map[hash_user_col] = USER_COLUMN
    if rename_map:
        df = df.rename(columns=rename_map)
    return df

def map_target(y_series: pd.Series) -> pd.Series:
    mapping = {"won":1,"win":1,"yes":1,"1":1,"true":1,"lost":0,"loss":0,"no":0,"0":0,"false":0}
    return y_series.astype(str).str.strip().str.lower().map(mapping)

def make_onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore",drop="first",sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore",drop="first",sparse=False)

def create_preprocessor(numerical_cols,categorical_cols,scale_numerical=True):
    transformers=[]
    if numerical_cols:
        num_steps=[("imputer",SimpleImputer(strategy="median"))]
        if scale_numerical:
            num_steps.append(("scaler",StandardScaler()))
        transformers.append(("num",Pipeline(num_steps),numerical_cols))
    if categorical_cols:
        transformers.append(("cat",Pipeline([("imputer",SimpleImputer(strategy="most_frequent")),("encoder",make_onehot_encoder())]),categorical_cols))
    return ColumnTransformer(transformers=transformers,remainder="drop")

def add_feature_engineering(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    df = df.copy()
    engineered_columns: List[str] = []
    offer_date_col = find_column_ignore_case(df.columns,"Offer Date")
    if offer_date_col is not None:
        offer_dates = pd.to_datetime(df[offer_date_col],errors="coerce")
        df["Offer_Year"]=offer_dates.dt.year; df["Offer_Month"]=offer_dates.dt.month; df["Offer_Quarter"]=offer_dates.dt.quarter
        engineered_columns.extend(["Offer_Year","Offer_Month","Offer_Quarter"])
        df=df.drop(columns=[offer_date_col])
    price_col=find_column_ignore_case(df.columns,PRICE_COLUMN)
    if price_col is not None:
        price_numeric=pd.to_numeric(df[price_col],errors="coerce")
        df["Price_Log"]=np.log1p(price_numeric.clip(lower=0))
        engineered_columns.append("Price_Log")
    else:
        price_numeric=None
    user_col=find_column_ignore_case(df.columns,USER_COLUMN)
    if user_col is not None:
        user_numeric=pd.to_numeric(df[user_col],errors="coerce")
        df["User_Log"]=np.log1p(user_numeric.clip(lower=0))
        engineered_columns.append("User_Log")
        if price_numeric is not None:
            safe_users=user_numeric.replace(0,np.nan)
            df["Price_Per_User"]=price_numeric/safe_users
            df["Price_Per_User"]=df["Price_Per_User"].replace([np.inf,-np.inf],np.nan)
            df["Price_Per_User_Log"]=np.log1p(df["Price_Per_User"].clip(lower=0))
            engineered_columns.extend(["Price_Per_User","Price_Per_User_Log"])
    competition_col=find_column_ignore_case(df.columns,"Competition")
    if competition_col is not None:
        ct=df[competition_col].fillna("").astype(str).str.strip()
        df["Has_Competition"]=((ct!="")&(ct.str.lower()!="nan")).astype(float)
        df["Competition_Count"]=ct.apply(lambda x:len([p for p in x.replace(";",",").split(",") if p.strip()]) if x and x.lower()!="nan" else 0)
        engineered_columns.extend(["Has_Competition","Competition_Count"])
    partner_col=find_column_ignore_case(df.columns,"Partner")
    if partner_col is not None:
        pt=df[partner_col].fillna("").astype(str).str.strip()
        df["Has_Partner"]=((pt!="")&(pt.str.lower()!="nan")).astype(float)
        engineered_columns.append("Has_Partner")
    product_col=find_column_ignore_case(df.columns,"Product")
    opp_type_col=find_column_ignore_case(df.columns,OPPORTUNITY_TYPE_COLUMN)
    if product_col is not None and opp_type_col is not None:
        df["Product_Opportunity_Type"]=df[product_col].fillna("missing").astype(str)+" | "+df[opp_type_col].fillna("missing").astype(str)
        engineered_columns.append("Product_Opportunity_Type")
    sector_col=find_column_ignore_case(df.columns,"Sector")
    source_col=find_column_ignore_case(df.columns,"Opportunity Source")
    if sector_col is not None and source_col is not None:
        df["Sector_Source"]=df[sector_col].fillna("missing").astype(str)+" | "+df[source_col].fillna("missing").astype(str)
        engineered_columns.append("Sector_Source")
    project_end_col=find_column_ignore_case(df.columns,"Estimated Project End Quarter")
    if project_end_col is not None:
        pe=df[project_end_col].astype(str).str.strip()
        df["Project_End_Known"]=((pe!="")&(pe.str.lower()!="nan")).astype(float)
        engineered_columns.append("Project_End_Known")
    return df,engineered_columns

def classify_features(data_dict):
    X=data_dict["X"]; all_columns=list(X.columns)
    manual_engineered=[c for c in MANUAL_ENGINEERED_FEATURES if c in all_columns]
    generated_engineered=[c for c in data_dict.get("engineered_columns",[]) if c in all_columns and c not in manual_engineered]
    raw_features=[c for c in all_columns if c not in manual_engineered and c not in generated_engineered]
    return raw_features,manual_engineered,generated_engineered

def _build_model_for_feature_list(X,feature_list):
    num=[c for c in feature_list if pd.api.types.is_numeric_dtype(X[c])]
    cat=[c for c in feature_list if c not in num]
    return Pipeline([("preprocessor",create_preprocessor(num,cat,True)),("classifier",LogisticRegression(penalty="l2",solver="lbfgs",C=1.0,random_state=RANDOM_STATE,class_weight="balanced",max_iter=5000))])

def evaluate_feature_additions(data_dict):
    X=data_dict["X"].copy(); y=data_dict["y"].copy()
    raw_cols,manual_engineered,generated_engineered=classify_features(data_dict)
    engineered_cols=manual_engineered+generated_engineered
    cv=StratifiedKFold(n_splits=CV_FOLDS,shuffle=True,random_state=RANDOM_STATE)
    if not raw_cols:
        return pd.DataFrame({"Feature":engineered_cols,"Feature_Source":["MANUAL_ENGINEERED" if c in manual_engineered else "GENERATED_ENGINEERED" for c in engineered_cols],"Baseline_RAW_ROC_AUC":[0.5]*len(engineered_cols),"RAW_plus_Feature_ROC_AUC":[0.5]*len(engineered_cols),"Delta_ROC_AUC":[0.0]*len(engineered_cols),"Keep?":["KEEP"]*len(engineered_cols)})
    baseline_mean=float(cross_val_score(_build_model_for_feature_list(X,raw_cols),X[raw_cols],y,cv=cv,scoring="roc_auc",n_jobs=N_JOBS).mean())
    rows=[]
    for feat in engineered_cols:
        if feat not in X.columns: continue
        tf=raw_cols+[feat]; scores=cross_val_score(_build_model_for_feature_list(X,tf),X[tf],y,cv=cv,scoring="roc_auc",n_jobs=N_JOBS); ms=float(scores.mean())
        rows.append({"Feature":feat,"Feature_Source":"MANUAL_ENGINEERED" if feat in manual_engineered else "GENERATED_ENGINEERED","Baseline_RAW_ROC_AUC":baseline_mean,"RAW_plus_Feature_ROC_AUC":ms,"Delta_ROC_AUC":ms-baseline_mean,"Keep?":"KEEP" if ms>baseline_mean else "DROP"})
    return pd.DataFrame(rows).sort_values("Delta_ROC_AUC",ascending=False).reset_index(drop=True)

def build_final_feature_set(data_dict,impact_df):
    raw_cols,manual_engineered,generated_engineered=classify_features(data_dict)
    kept=[]; dropped=[]
    if not impact_df.empty:
        kept=impact_df.loc[impact_df["Keep?"]=="KEEP","Feature"].tolist()
        dropped=impact_df.loc[impact_df["Keep?"]=="DROP","Feature"].tolist()
    final=raw_cols+kept
    final_df=pd.DataFrame({"Feature":final,"Feature_Type":["RAW" if c in raw_cols else "KEEP" for c in final],"Feature_Source":["RAW" if c in raw_cols else "MANUAL_ENGINEERED" if c in manual_engineered else "GENERATED_ENGINEERED" if c in generated_engineered else "UNKNOWN" for c in final]})
    dropped_df=pd.DataFrame({"Dropped_Engineered_Features":dropped,"Feature_Source":["MANUAL_ENGINEERED" if c in manual_engineered else "GENERATED_ENGINEERED" for c in dropped]})
    return final,final_df,dropped_df

def _get_comparison_models_and_grids():
    models={"Logistic Regression":LogisticRegression(penalty=None,solver="lbfgs",random_state=RANDOM_STATE,class_weight="balanced",max_iter=5000),"Ridge Logistic Regression":LogisticRegression(penalty="l2",solver="lbfgs",random_state=RANDOM_STATE,class_weight="balanced",max_iter=5000),"Lasso Logistic Regression":LogisticRegression(penalty="l1",solver="liblinear",random_state=RANDOM_STATE,class_weight="balanced",max_iter=5000),"Elastic Net Logistic Regression":LogisticRegression(penalty="elasticnet",solver="saga",random_state=RANDOM_STATE,class_weight="balanced",max_iter=5000),"Random Forest":RandomForestClassifier(random_state=RANDOM_STATE,class_weight="balanced"),"Gradient Boosting":GradientBoostingClassifier(random_state=RANDOM_STATE)}
    param_grids={"Logistic Regression":{},"Ridge Logistic Regression":{"classifier__C":[0.01,0.1,1,10,100]},"Lasso Logistic Regression":{"classifier__C":[0.01,0.1,1,10,100]},"Elastic Net Logistic Regression":{"classifier__C":[0.01,0.1,1,10,100],"classifier__l1_ratio":[0.1,0.5,0.9]},"Random Forest":{"classifier__n_estimators":[100,200],"classifier__max_depth":[None,10,20]},"Gradient Boosting":{"classifier__n_estimators":[100,200],"classifier__learning_rate":[0.01,0.1],"classifier__max_depth":[3,5]}}
    return models,param_grids

def _build_pipeline_for_feature_subset(feature_names,X,estimator):
    num=[c for c in feature_names if pd.api.types.is_numeric_dtype(X[c])]
    cat=[c for c in feature_names if c not in num]
    scale=not isinstance(estimator,(RandomForestClassifier,GradientBoostingClassifier))
    return Pipeline([("preprocessor",create_preprocessor(num,cat,scale)),("classifier",estimator)])

def train_feature_subset_nested_cv(feature_set_name,feature_names,X,y):
    base_models,param_grids=_get_comparison_models_and_grids()
    results={}
    outer_cv=StratifiedKFold(n_splits=NESTED_OUTER_FOLDS,shuffle=True,random_state=RANDOM_STATE)
    inner_cv=StratifiedKFold(n_splits=NESTED_INNER_FOLDS,shuffle=True,random_state=RANDOM_STATE)
    for name,estimator in base_models.items():
        outer_fold_metrics=[]; outer_best_params=[]
        for fold_no,(train_idx,test_idx) in enumerate(outer_cv.split(X[feature_names],y),start=1):
            X_train=X.iloc[train_idx][feature_names].copy(); X_test=X.iloc[test_idx][feature_names].copy()
            y_train=y.iloc[train_idx].copy(); y_test=y.iloc[test_idx].copy()
            pipe=_build_pipeline_for_feature_subset(feature_names,X,estimator)
            grid=GridSearchCV(estimator=pipe,param_grid=param_grids.get(name,{}),cv=inner_cv,scoring="roc_auc",n_jobs=N_JOBS,verbose=0,refit=True)
            grid.fit(X_train,y_train); best_model=grid.best_estimator_
            y_pred=best_model.predict(X_test); y_proba=best_model.predict_proba(X_test)[:,1]
            outer_fold_metrics.append({"Outer Fold":fold_no,"ROC-AUC":float(roc_auc_score(y_test,y_proba)),"Accuracy":float(accuracy_score(y_test,y_pred)),"Precision":float(precision_score(y_test,y_pred,zero_division=0)),"Recall":float(recall_score(y_test,y_pred,zero_division=0)),"F1-score":float(f1_score(y_test,y_pred,zero_division=0)),"Best Params":grid.best_params_})
            outer_best_params.append(str(grid.best_params_))
        fold_df=pd.DataFrame(outer_fold_metrics)
        results[name]={"Feature Set":feature_set_name,"Model Name":name,"Fold Results":fold_df,"Nested CV Mean ROC-AUC":float(fold_df["ROC-AUC"].mean()),"Nested CV Std ROC-AUC":float(fold_df["ROC-AUC"].std()),"Nested CV Mean Accuracy":float(fold_df["Accuracy"].mean()),"Nested CV Mean Precision":float(fold_df["Precision"].mean()),"Nested CV Mean Recall":float(fold_df["Recall"].mean()),"Nested CV Mean F1-score":float(fold_df["F1-score"].mean()),"Best Params Per Fold":outer_best_params}
    return results

def get_representative_best_params(model_results):
    if not model_results or "Fold Results" not in model_results: return {}
    params_series=model_results["Fold Results"]["Best Params"].dropna()
    if params_series.empty: return {}
    counts={}
    for params in params_series:
        key=tuple(sorted(params.items())); counts[key]=counts.get(key,0)+1
    return dict(max(counts.items(),key=lambda item:item[1])[0])

def build_lasso_price_probability_model(X,y,selected_features,all_subset_results,price_col):
    if price_col not in X.columns or price_col not in selected_features: return None,None
    lasso_results=all_subset_results.get("Selected Features",{}).get("Lasso Logistic Regression")
    best_params=get_representative_best_params(lasso_results)
    lasso=LogisticRegression(penalty="l1",solver="liblinear",random_state=RANDOM_STATE,class_weight="balanced",max_iter=5000,C=best_params.get("classifier__C",1.0))
    pipe=_build_pipeline_for_feature_subset(selected_features,X,lasso)
    pipe.fit(X[selected_features],y)
    base_scenario={}
    for col in selected_features:
        if pd.api.types.is_numeric_dtype(X[col]):
            base_scenario[col]=float(pd.to_numeric(X[col],errors="coerce").median())
        else:
            mode=X[col].mode(dropna=True); base_scenario[col]=mode.iloc[0] if not mode.empty else "missing"
    return pipe,base_scenario

def predict_win_probability_for_price(model,scenario,selected_features,price_col,input_price):
    row=scenario.copy(); row[price_col]=float(input_price)
    user_value=row.get(USER_COLUMN)
    if "Price_Log" in selected_features: row["Price_Log"]=float(np.log1p(max(input_price,0)))
    if "Price_Per_User" in selected_features and user_value is not None and pd.notna(user_value) and float(user_value)>0: row["Price_Per_User"]=input_price/float(user_value)
    if "Price_Per_User_Log" in selected_features and user_value is not None and pd.notna(user_value) and float(user_value)>0: row["Price_Per_User_Log"]=float(np.log1p(max(input_price/float(user_value),0)))
    row_df=pd.DataFrame([row])[selected_features]
    return float(model.predict_proba(row_df)[0,1])

def build_prediction_scenario(user_inputs,selected_features,base_scenario,engineered_columns):
    scenario=base_scenario.copy()
    if not user_inputs: return scenario
    for col in selected_features:
        if col in _AUTO_FEATURES: continue
        val=user_inputs.get(col)
        if val is None or str(val).strip()=="": continue
        base_val=base_scenario.get(col)
        if isinstance(base_val,(int,float)):
            try: scenario[col]=float(str(val).replace(",",".")); continue
            except (TypeError,ValueError): pass
        scenario[col]=str(val)
    return scenario

def build_fast_pipeline(selected_features: List[str], X: pd.DataFrame) -> Pipeline:
    """
    Fast production training pipeline — no grid search, no nested CV.
    Lasso LogisticRegression with C=1.0, fixed hyperparameters.
    Completes in seconds instead of minutes.
    """
    numerical_cols = [c for c in selected_features if pd.api.types.is_numeric_dtype(X[c])]
    categorical_cols = [c for c in selected_features if c not in numerical_cols]
    preprocessor = create_preprocessor(numerical_cols, categorical_cols, scale_numerical=True)
    lasso = LogisticRegression(
        penalty="l1",
        solver="liblinear",
        C=1.0,
        random_state=RANDOM_STATE,
        class_weight="balanced",
        max_iter=5000,
    )
    return Pipeline([("preprocessor", preprocessor), ("classifier", lasso)])
