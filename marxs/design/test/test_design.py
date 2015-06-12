import numpy as np

from ..rowland import RowlandTorus, GratingArrayStructure

def parametrictorus(R, r, theta, phi):
    x = (R + r * np.cos(theta)) * np.cos(phi)
    y = (R + r * np.cos(theta)) * np.sin(phi)
    z = r * np.sin(theta)
    return x, y, z

def test_torus():
    '''Test the torus equation for a set of points.

    Importantly, we use a parametric description of the torus here, which is
    different from the actual implementation.
    '''
    R = 2.
    r = 1.

    angle = np.arange(0, 2 * np.pi, 0.1)
    phi, theta = np.meshgrid(angle, angle)
    phi = phi.flatten()
    theta = theta.flatten()
    x, y, z = parametrictorus(R, r, theta, phi)
    mytorus = RowlandTorus(R=R, r=r)

    assert np.allclose(mytorus.quartic(x, y, z), 0.)

def test_torus_normal():
    '''Compare the analytic normal with a numeric result.

    The test computes a vector along the torus for small d_theta
    and d_phi. Both of those should be perpendicular to the normal.
    '''
    R = 2.
    r = 1.

    angle = np.arange(0, 2 * np.pi, 0.1)
    phi, theta = np.meshgrid(angle, angle)
    phi = phi.flatten()
    theta = theta.flatten()
    x, y, z = parametrictorus(R, r, theta, phi)
    xt1, yt1, zt1 = parametrictorus(R, r, theta + 0.001, phi)
    xp1, yp1, zp1 = parametrictorus(R, r, theta, phi + 0.001)
    xt0, yt0, zt0 = parametrictorus(R, r, theta - 0.001, phi)
    xp0, yp0, zp0 = parametrictorus(R, r, theta, phi + 0.001)

    mytorus = RowlandTorus(R=R, r=r)
    vec_normal = np.vstack(mytorus.normal(x, y, z))

    vec_delta_theta = np.vstack([xt1 - xt0, yt1 - yt0, zt1 - zt0])
    vec_delta_phi = np.vstack([xp1 - xp0, yp1 - yp0, zp1 - zp0])

    assert np.allclose(np.einsum('ij,ij->j', vec_normal, vec_delta_theta), 0.)
    assert np.allclose(np.einsum('ij,ij->j', vec_normal, vec_delta_phi), 0.)

def test_GratingArrayStructure():
    '''Check a GAS for consistency

    The expected numbers for this one are hand-checked and plotted and thus
    can be taken as known-good to prevent regressions later.
    '''
    myrowland = RowlandTorus(10000., 10000.)
    gas = GratingArrayStructure(myrowland, 30., [10000., 20000.], [300., 600.], phi = [-0.2*np.pi, 0.2*np.pi])
    assert gas.max_facets_on_arc(300.) == 12
    angles = gas.distribute_facets_on_arc(315.) % (2. * np.pi)
    # This is a wrap-around case. Hard to test in general, but here I know the numbers
    assert np.alltrue((angles < 0.2 * np.pi) | (angles > 1.8 * np.pi))
    assert gas.max_facets_on_radius() == 10
    assert np.all(gas.distribute_facets_on_radius() == np.arange(315., 600., 30.))
    assert len(gas.facets) == 177
    # fig, axes = plt.subplots(2,2)
    # for elem in [[axes[0, 0], 0, 1], [axes[0, 1], 0, 2], [axes[1, 0], 1, 2]]:
    #     for f in gas.facets:
    #         elem[0].plot(f[elem[1],3], f[elem[2],3], 's')
    # plt.show()  # or move mouse in window or something.

    # There is a test missing here that the rotational part works correctly.
    # I just cannot think of a good way to check that right now.

