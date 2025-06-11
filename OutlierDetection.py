import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

def clustering_of_negative_samples(df, Cu_column_name, As_column_name, data_type):

    data = df.drop(columns=['Well'])
    names = df['Well']

    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)

    #pca = PCA(n_components=2)
    #pca_result = pca.fit_transform(data_scaled)

    dbscan = DBSCAN(eps=0.12, min_samples=5)
    labels = dbscan.fit_predict(data_scaled)

    outlier_indices = np.where(labels == -1)[0]
    outliers = names[outlier_indices]



    def assign_samples_to_subgroups(raw_data, outliers, copper_ratio_threshold=5, arsenic_ratio_threshold=0.2):
        """
        Filters out samples from the outliers where the copper-to-arsenic ratio is heavily skewed toward copper.

        Parameters:
            raw_data (pd.DataFrame): Original dataset with columns ['Sample', 'Copper', 'Arsenic'].
            outliers (pd.Series): Series containing the names of outlier samples.
            copper_ratio_threshold (float): Threshold above which the ratio is considered skewed to copper.

        Returns:
            pd.Series: Names of samples with copper-skewed ratios.
        """
        outlier_data = raw_data[raw_data['Well'].isin(outliers)]

        # Calculate the copper-to-arsenic ratio
        outlier_data['Cu_As_Ratio'] = outlier_data[Cu_column_name] / outlier_data[As_column_name]

        # Filter for copper-skewed samples
        if data_type != 'µXRF':
            copper_skewed = outlier_data[outlier_data['Cu_As_Ratio'] > copper_ratio_threshold]
        else:
            copper_skewed = outlier_data[outlier_data[As_column_name] == 0.0]
        copper_skewed.rename(columns={'Well': 'Group 2'}, inplace=True)
        copper_skewed.reset_index(drop=True, inplace=True)
        copper_skewed_len = len(copper_skewed['Group 2'])
        copper_skewed.drop('Cu_As_Ratio', axis=1, inplace=True)

        # Filter for arsenic-skewed samples
        if data_type != 'µXRF':
            arsenic_skewed = outlier_data[outlier_data['Cu_As_Ratio'] < arsenic_ratio_threshold]
        else:
            arsenic_skewed = outlier_data[outlier_data[Cu_column_name] == 0.0]
        arsenic_skewed.rename(columns={'Well': 'Group 3'}, inplace=True)
        arsenic_skewed.reset_index(drop=True, inplace=True)
        arsenic_skewed_len = len(arsenic_skewed['Group 3'])
        arsenic_skewed.drop('Cu_As_Ratio', axis=1, inplace=True)

        if data_type != 'µXRF':
            normal_outliers = outlier_data[outlier_data['Cu_As_Ratio'] < copper_ratio_threshold]
        else:
            normal_outliers = outlier_data[(outlier_data[As_column_name] > 0.0) & (outlier_data[Cu_column_name] > 0.0)]
        normal_outliers = normal_outliers[arsenic_ratio_threshold < outlier_data['Cu_As_Ratio']]
        normal_outliers.rename(columns={'Well': 'Group 4'}, inplace=True)
        normal_outliers.reset_index(drop=True, inplace=True)
        normal_outliers_len = len(normal_outliers['Group 4'])
        normal_outliers.drop('Cu_As_Ratio', axis=1, inplace=True)

        base_group = df[~df['Well'].isin(outliers)]
        base_group.rename(columns={'Well': 'Group 1'}, inplace=True)
        base_group.reset_index(drop=True, inplace=True)
        base_group_len = len(base_group['Group 1'])

        len_dict = {}
        len_dict['len_copper_skewed'] = copper_skewed_len
        len_dict['len_arsenic_skewed'] = arsenic_skewed_len
        len_dict['len_normal_outliers'] = normal_outliers_len
        len_dict['len_base_group'] = base_group_len

        merged_groups_df = pd.concat([base_group, copper_skewed, arsenic_skewed, normal_outliers], axis=1)

        return copper_skewed['Group 2'], arsenic_skewed['Group 3'], normal_outliers['Group 4'], base_group['Group 1'], merged_groups_df, len_dict


    # Call the function
    copper_skewed_outliers, arsenic_skewed_outliers, normal_outliers, base_group, merged_groups_df, len_dict = assign_samples_to_subgroups(df, outliers)

    return copper_skewed_outliers, arsenic_skewed_outliers, normal_outliers, base_group, merged_groups_df, len_dict









