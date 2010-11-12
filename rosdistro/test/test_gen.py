import roslib; roslib.load_manifest("rosdistro")
import rosdistro
import yaml


release_name = 'unstable'
uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%release_name

distro = rosdistro.Distro(uri)


print 'ros', distro.stacks['ros'].repo
print 'nxt', distro.stacks['nxt'].repo
print 'pr2_doors', distro.stacks['pr2_doors'].repo

print 'geometry', distro.stacks['geometry'].repo


for s in distro.stack_names:
    print s, distro.stacks[s].repo

print "geometry"
print yaml.dump(rosdistro.stack_to_rosinstall(distro.stacks['geometry'], "distro"))
print "nxt distro"
print yaml.dump(rosdistro.stack_to_rosinstall(distro.stacks['nxt'], "distro"))
print "nxt release"
print yaml.dump(rosdistro.stack_to_rosinstall(distro.stacks['nxt'], "release"))
print "pr2all"
print yaml.dump( rosdistro.variant_to_rosinstall("pr2all", distro, "distro"))
print "distro"
print yaml.dump( rosdistro.distro_to_rosinstall(distro, "distro"))


