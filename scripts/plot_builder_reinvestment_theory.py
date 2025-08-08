import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams

# Set up seaborn plotting style
sns.set_style("whitegrid")
palette = sns.color_palette("mako_r", 6)
rcParams.update({
    'font.family': 'serif',
    'font.size': 14,
    'axes.labelsize': 18,
    'xtick.labelsize': 16,
    'ytick.labelsize': 16,
    'legend.fontsize': 14
})

def builder_growth_rate(f_pi, S_Bi, total_stake, gamma_Bi, v_i_T):
    """Calculate the builder growth rate based on the derived formula."""
    term1 = v_i_T * (1 - f_pi) / total_stake
    term2 = f_pi * v_i_T / S_Bi
    growth_rate = 1 + gamma_Bi * (term1 + term2)
    return growth_rate

def create_builder_growth_theory_plot():
    """Create the theoretical plot showing builder growth rate vs f·π for different stake levels."""
    
    # Parameters
    f_pi_range = np.linspace(0, 1, 200)
    total_stake = 1000
    gamma_Bi = 0.8
    v_i_T = 10
    
    # Different initial stake levels (as percentages of total stake)
    stake_percentages = [0.01, 0.05, 0.1, 0.2, 0.5]
    stake_values = [total_stake * pct for pct in stake_percentages]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot each stake level
    for i, S_Bi in enumerate(stake_values):
        growth_rates = []
        for f_pi in f_pi_range:
            growth_rate = builder_growth_rate(f_pi, S_Bi, total_stake, gamma_Bi, v_i_T)
            growth_rates.append(growth_rate)
        
        sns.lineplot(x=f_pi_range, y=growth_rates, 
                    label=f'{stake_percentages[i]*100:.0f}%',
                    linewidth=2.5, ax=ax, color=palette[i])
    
    # Add horizontal line at growth rate = 1
    ax.axhline(y=1, color='black', linestyle='--', alpha=0.7, linewidth=1.5, 
               label='No Growth')
    
    # Customize the plot
    ax.set_xlabel(r'Builder Ability $f \cdot \pi$', fontsize=16)
    ax.set_ylabel(r'Builder Growth Rate $\frac{s_{B_i}(\ell+1)}{s_{B_i}(\ell)}$', fontsize=16)
    ax.set_xlim(0, 1)
    ax.set_ylim(1.0, 1.8)
    
    # Legend in top left with more space
    ax.legend(title=r'Builder Stake $s_{B_i}$', title_fontsize=13, fontsize=12, 
             loc='upper left', frameon=True, fancybox=False, shadow=False,
             bbox_to_anchor=(0.02, 0.98))
    
    # Parameters (vertical list, before equation)
    param_text = (r'Parameters:' + '\n' + 
                 r'$\gamma_{B_i} = 0.8$' + '\n' + 
                 r'$v_{i,\tau} = 10$' + '\n' + 
                 r'$\sum_j s_j = 1000$')
    ax.text(0.25, 0.95, param_text, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', 
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9))
    
    # Formula annotation (after parameters, moved more to the left)
    formula_text = (r'$\frac{s_{B_i}(\ell+1)}{s_{B_i}(\ell)} = 1 + \gamma_{B_i} \left[\frac{v_{i,\tau}(1 - f\pi)}{\sum_j s_j} + \frac{f\pi v_{i,\tau}}{s_{B_i}}\right]$')
    ax.text(0.45, 0.95, formula_text, transform=ax.transAxes, fontsize=16,
            verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9))
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    fig = create_builder_growth_theory_plot()
    fig.savefig('../figures/theory/builder_growth_rate.png', bbox_inches='tight', dpi=300)
    print("Builder growth rate theory plot generated successfully!")
    print("File saved: ../figures/theory/builder_growth_rate.png")
    plt.show() 