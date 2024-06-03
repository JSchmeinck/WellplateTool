import matplotlib.pyplot as plt
import matplotlib as mpl



yellow = mpl.colors.LinearSegmentedColormap.from_list(name='Yellow',
                                                           colors=['white', '#f5e216'])
plt.register_cmap(cmap=yellow)

blue = mpl.colors.LinearSegmentedColormap.from_list(name='Blue',
                                                           colors=['white', '#1520eb'])
plt.register_cmap(cmap=blue)

red = mpl.colors.LinearSegmentedColormap.from_list(name='Red',
                                                           colors=['white', '#eb1515'])
plt.register_cmap(cmap=red)

cyan = mpl.colors.LinearSegmentedColormap.from_list(name='Cyan',
                                                           colors=['white', '#15ebeb'])
plt.register_cmap(cmap=cyan)

green = mpl.colors.LinearSegmentedColormap.from_list(name='Green',
                                                           colors=['white', '#15eb4e'])
plt.register_cmap(cmap=green)

darkgreen = mpl.colors.LinearSegmentedColormap.from_list(name='Dark Green',
                                                           colors=['white', '#0c6b25'])
plt.register_cmap(cmap=darkgreen)

orange = mpl.colors.LinearSegmentedColormap.from_list(name='Orange',
                                                           colors=['white', '#eb7515'])
plt.register_cmap(cmap=orange)