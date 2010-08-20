package Yuki::PluginManager;

use UNIVERSAL qw(can);

# Be careful.
# use strict;
# no strict refs;

my $VERSION = '0.2';
my $DEBUG = 0;

#
# Constructor of Yuki::PluginManager.
#
sub new {
    my ($class, $context, @dirs) = @_;
    my $self = {
        # Maps plugin name to its filename.
        pluginname_to_filename => {},
        # Listing of filter type plugins.
        filter => [],
        # Logs.
        log => [],
        # Plugin context given by YukiWiki plugin.
        context => $context,
    };
    # Search for plugins.
    for my $dir (@dirs) {
        for my $file (sort glob("$dir/*.pl")) {
            if (-e($file)) {
                my $pluginname = $file;
                $pluginname =~ s/.*?(\w+?)\.pl$/$1/;
                $self->{pluginname_to_filename}->{$pluginname} = $file;
                if ($plugin =~ /^filter_/) {
                    push(@{$self->{filter}}, $plugin);
                }
            }
        }
    }
    return bless $self, $class;
}

# Calls plugin.
# $plugin is the plugin name, for example: 'amazon'
# $type is either 'inline', 'block', 'usage, or 'filter'.
# $argument is plugin dependent.
sub call {
    my ($self, $plugin, $type, $argument) = @_;
    my $file = $self->{pluginname_to_filename}->{$plugin};
    my $result = undef;
    # <use-can>
    # my $funcname = "plugin_$type";
    # my $funcref = \&{"${plugin}::plugin_$type"};
    # my $namespace = \%{"${plugin}::"};
    # </use-can>
    # Does the plugin exist?
    if ($file) {
        eval {
            require $file;
            # Check if the function is defined or not.
            # <use-can>
            # if (defined($namespace->{$funcname})) {
            #     $result = $funcref->($argument, $self->{context});
            # } else {
            #     push(@{$self->{log}}, "$funcname: undefined function.");
            # }
            # </use-can>
            my $funcname = "plugin_$type";
            my $funcref = can($plugin, $funcname);
            if (defined($funcref)) {
                $result = $funcref->($argument, $self->{context});
            } else {
                push(@{$self->{log}}, "$funcname: undefined function.");
            }
        };
        if ($@) {
            push(@{$self->{log}}, "$@");
        }
    } else {
        push(@{$self->{log}}, "$plugin: file for this plugin is not found.");
    }
    return $result;
}

# Return undef if no replacement.
sub filter {
    my ($self) = @_;
    for my $plugin (@{$self->{filter}}) {
        my $rawout = $self->call($plugin, 'filter', '');
        return $rawout if defined($rawout);
    }
    return undef;
}

# Gather information of plugins.
sub usage {
    my ($self) = @_;
    my $usage_array_ref = [];
    for my $plugin (sort keys %{$self->{pluginname_to_filename}}) {
        my $usage_hash = $self->call($plugin, 'usage', '');
        if (defined($usage_hash)) {
            push(@{$usage_array_ref}, $usage_hash);
        }
    }
    return $usage_array_ref;
}

1;
__END__
=head1 NAME

Yuki::PluginManager - Manages installed YukiWiki plugins.

=head1 SYNOPSIS

    use strict;
    use Yuki::PluginManager;

    my $plugin_manager = new Yuki::PluginManager($plugin_context, 'plugin/dir/');

=head1 DESCRIPTION

Yuki::PluginManager is used by YukiWiki.

=head1 METHODS

=over 4

=item new($plugin_context, @dirs)

=item call($self, $plugin, $type, $argument)

It calls $plugin::plugin_$type($argument).

=head1 SEE ALSO

=back

=head1 AUTHOR

Hiroshi Yuki <hyuki@hyuki.com> http://www.hyuki.com/

=head1 LICENSE

Copyright (C) 2003, 2004 by Hiroshi Yuki.

This program is free software; you can redistribute it and/or
modify it under the same terms as Perl itself.

=cut
