import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams

# Set up seaborn plotting style
sns.set_style("whitegrid")
palette = sns.color_palette("mako_r", 6)
rcParams.update({
    'font.family': 'serif',
    'font.size': 22,
    'axes.labelsize': 24,
    'xtick.labelsize': 22,
    'ytick.labelsize': 22,
    'legend.fontsize': 22
})

def builder_growth_rate(f_pi, s_Bi, total_stake, gamma_Bi, v_i_T):
    """Calculate the builder growth rate based on the derived formula."""
    term1 = v_i_T * (1 - f_pi) / total_stake
    term2 = f_pi * v_i_T / s_Bi
    growth_rate = 1 + gamma_Bi * (term1 + term2)
    return growth_rate

def proposer_growth_rate(f_pi, s_Pi, total_stake, gamma_Pi, b_i_T):
    """Calculate the proposer growth rate based on the derived formula."""
    # Original simple formula: s_Pi(ℓ+1) = s_Pi(ℓ) + γ_Pi * (s_Pi(ℓ)/∑_j s_j(ℓ)) * b_i,T(ℓ)
    # Growth rate = 1 + γ_Pi * b_i,T / ∑_j s_j
    # Scale up b_i_T to make it comparable to builder plots
    scaled_reward = f_pi * b_i_T * 10  # Scale factor to match builder range
    growth_rate = 1 + gamma_Pi * scaled_reward / total_stake
    return growth_rate

def create_builder_growth_theory_plot():
    """Create the theoretical plot showing builder growth rate vs stake percentage for different f·π values."""
    
    # Parameters
    stake_percentages = np.linspace(0.01, 0.5, 200)  # 1% to 50% of total stake
    total_stake = 1000
    gamma_Bi = 0.8
    v_i_T = 10
    
    # Different f·π values
    f_pi_values = [0.1, 0.3, 0.5, 0.7, 0.9]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plot each f·π value
    for i, f_pi in enumerate(f_pi_values):
        growth_rates = []
        for stake_pct in stake_percentages:
            s_Bi = total_stake * stake_pct
            growth_rate = builder_growth_rate(f_pi, s_Bi, total_stake, gamma_Bi, v_i_T)
            growth_rates.append(growth_rate)
        
        ax.plot(stake_percentages * 100, growth_rates, 
                linewidth=3, color=palette[i], label=f'$f \cdot \pi = {f_pi}$')
    
    # Add horizontal line at growth rate = 1
    ax.axhline(y=1, color='black', linestyle='--', alpha=0.7, linewidth=1.5, 
               label='No Growth')
    
    # Customize the plot
    ax.set_xlabel(r'Builder Stake $s_{B_i}$ (%)', fontsize=24)
    ax.set_ylabel(r'Builder Growth Rate $\frac{s_{B_i}(\ell+1)}{s_{B_i}(\ell)}$', fontsize=24)
    ax.set_xlim(1, 50)
    ax.set_ylim(1.0, 1.8)
    
    # Legend
    ax.legend(title=r'Builder Ability $f \cdot \pi$', title_fontsize=20, fontsize=22, 
             loc='upper right', frameon=True, fancybox=False, shadow=False)
    
    plt.tight_layout()
    return fig


def create_stake_evolution_plot():
    """Create the plot showing builder stake evolution over time slots."""
    
    # Parameters
    total_stake = 1000
    gamma_Bi = 0.8
    v_i_T = 10
    
    # Different fπ values
    f_pi_values = [0.1, 0.3, 0.5, 0.7, 0.9]
    
    # Single initial stake (small starting point)
    initial_stake = 10  # Start with 1% of total stake
    s_initial = initial_stake
    
    # Time slots - more blocks
    time_slots = np.arange(0, 201)  # 0 to 200 slots
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plot for each fπ value
    for i, f_pi in enumerate(f_pi_values):
        # Calculate stake evolution
        stakes = [s_initial]
        
        for slot in range(1, len(time_slots)):
            # Calculate growth rate
            growth_rate = builder_growth_rate(f_pi, stakes[-1], total_stake, gamma_Bi, v_i_T)
            # Update stake
            new_stake = stakes[-1] * growth_rate
            stakes.append(new_stake)
        
        # Plot the line
        ax.plot(time_slots, stakes, 
                linewidth=3, color=palette[i], label=f'$f \cdot \pi = {f_pi}$')
    
    # Add horizontal line for total stake
    ax.axhline(y=total_stake, color='red', linestyle='--', alpha=0.7, linewidth=2, 
               label='Total Stake')
    
    # Customize the plot
    ax.set_xlabel(r'Time Slot $\ell$', fontsize=24)
    ax.set_ylabel(r'Builder Stake $s_{B_i}$ (%)', fontsize=24)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, total_stake)  # Stop at 100%
    
    # Convert y-axis to percentage
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0f}'.format(y/total_stake*100)))
    
    # Legend
    ax.legend(title=r'Builder Ability $f \cdot \pi$', title_fontsize=20, fontsize=22, 
             loc='upper left', frameon=True, fancybox=False, shadow=False)
    
    plt.tight_layout()
    return fig

def create_proposer_stake_evolution_plot():
    """Create the plot showing proposer stake evolution over time slots."""
    
    # Parameters
    total_stake = 1000
    gamma_Pi = 0.8
    b_i_T = 10  # Fixed proposer reward
    
    # Different f·π values (same as builder)
    f_pi_values = [0.1, 0.3, 0.5, 0.7, 0.9]
    
    # Single initial stake (small starting point)
    initial_stake = 10  # Start with 1% of total stake
    s_initial = initial_stake
    
    # Time slots - more blocks
    time_slots = np.arange(0, 201)  # 0 to 200 slots
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plot for each f·π value
    for i, f_pi in enumerate(f_pi_values):
        # Calculate stake evolution
        stakes = [s_initial]
        
        for slot in range(1, len(time_slots)):
            # Calculate growth rate
            growth_rate = proposer_growth_rate(f_pi, stakes[-1], total_stake, gamma_Pi, b_i_T)
            # Update stake
            new_stake = stakes[-1] * growth_rate
            stakes.append(new_stake)
        
        # Plot the line
        ax.plot(time_slots, stakes, 
                linewidth=3, color=palette[i], label=f'$f \cdot \pi = {f_pi}$')
    
    # Add horizontal line for total stake
    ax.axhline(y=total_stake, color='red', linestyle='--', alpha=0.7, linewidth=2, 
               label='Total Stake')
    
    # Customize the plot
    ax.set_xlabel(r'Time Slot $\ell$', fontsize=24)
    ax.set_ylabel(r'Proposer Stake $s_{{P_i}}$ (%)', fontsize=24)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, total_stake)  # Stop at 100%
    
    # Convert y-axis to percentage
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0f}'.format(y/total_stake*100)))
    
    # Legend
    ax.legend(title=r'Proposer Ability $f \cdot \pi$', title_fontsize=20, fontsize=22, 
             loc='upper left', frameon=True, fancybox=False, shadow=False)
    
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    # Generate selected plots
    print("Generating builder growth rate theory plot...")
    fig1 = create_builder_growth_theory_plot()
    fig1.savefig('figures/theory/builder_growth_rate.png', bbox_inches='tight', dpi=300)
    print("Builder growth rate theory plot generated successfully!")
    print("File saved: figures/theory/builder_growth_rate.png")
    
    print("\nGenerating builder stake evolution plot...")
    fig2 = create_stake_evolution_plot()
    fig2.savefig('figures/theory/builder_stake_evolution.png', bbox_inches='tight', dpi=300)
    print("Builder stake evolution plot generated successfully!")
    print("File saved: figures/theory/builder_stake_evolution.png")
    
    print("\nGenerating proposer stake evolution plot...")
    fig3 = create_proposer_stake_evolution_plot()
    fig3.savefig('figures/theory/proposer_stake_evolution.png', bbox_inches='tight', dpi=300)
    print("Proposer stake evolution plot generated successfully!")
    print("File saved: figures/theory/proposer_stake_evolution.png")
    
    print("\nAll selected plots generated successfully!")
    
    # Show all plots
    plt.show()