import sys
import toml
import matplotlib.pyplot as plt
import numpy as np

def plot_mesh(mesh_config, particle_params, show = False, outfile = None):
        _, ax = plt.subplots(figsize=(12,10))
        ax.tick_params(axis = 'both', which = 'major', labelsize = 20)
        ax.tick_params(axis = 'both', which = 'minor', labelsize = 20)

        # Coordinate Sets
        triangles = mesh_config['triangles']
        N = len(triangles) * 3
        mesh = np.zeros((N,2))
        for n in range(N):
            coords = triangles[n // 3]
            x, y = coords[n % 3], coords[(n % 3) + 3]
            mesh[n][0] = x
            mesh[n][1] = y

        for n in range(0,N,3):
            triangle = np.append(
                mesh[n:n+3],
                [list(mesh[n])],
                axis = 0,
            )
            plt.plot(triangle[:,0], triangle[:,1], 'b-')

        # Mesh Boundary
        mesh_boundary = np.array(mesh_config['material_boundary_points'])
        plt.plot(
            mesh_boundary[:,0],
            mesh_boundary[:,1],
            '*',
            label = 'mesh boundary',
        )


        # Simulation Boundary
        simulation_boundary = np.array(mesh_config['simulation_boundary_points'])
        plt.plot(
            simulation_boundary[:,0],
            simulation_boundary[:,1],
            '^',
            label = 'simulation_boundary',
        )

        # Plot All Particle Directions
        plotted_particle_starts = set()
        for x, v in list(zip(particle_params['pos'], particle_params['dir']))[::100]:
            if (x[0], x[1]) not in plotted_particle_starts:
                plt.plot(x[0], x[1], 'o')
                plotted_particle_starts.add((x[0], x[1]))
            v_norm = np.sqrt(np.dot(np.array(v), np.array(v)))
            arrow_end = x
            arrow_start = (x[0] + v[0], x[1] + v[1])
            plt.annotate('',
                xytext=(arrow_end[0],arrow_end[1]),
                xy=(arrow_start[0], arrow_start[1]),
                arrowprops=dict(facecolor='black', width = 0.5),
            )


        length_unit = mesh_config['length_unit'].lower()
        plt.title('2-D Simulation Mesh', fontsize = 20)
        plt.ylabel('y (%s)' % length_unit, fontsize = 20)
        plt.xlabel('x (%s)' % length_unit, fontsize = 20)
        plt.legend(prop = dict(size=16))

        if outfile is not None:
            plt.savefig(outfile, dpi = 300, bbox_inches = 'tight')
            print(f'saved to {outfile}')

        if show:
            print('showing..')
            plt.show()



if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        data = toml.load(f)

    plot_mesh(
        data['mesh_2d_input'],
        data['particle_parameters'],
        outfile = 'example-mesh.png'
    )
