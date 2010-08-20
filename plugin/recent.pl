use strict;

package recent;

sub plugin_block {
    my ($escaped_argument, $context) = @_;
    my ($count) = split(/,/, $escaped_argument);
    my @raw_recent_changes = split(/\n/, $context->{database}->{RecentChanges});
    my @recent_changes = splice(@raw_recent_changes, 0, $count);
    my $recent_changes = join("\n", @recent_changes);
    my $result = &main::text_to_html($recent_changes, toc=>0);
    return $result;
}

sub plugin_usage {
    return {
        name => 'recent',
        version => '1.0',
        author => 'Hiroshi Yuki <hyuki@hyuki.com>',
        syntax => '#recent(count)',
        description => 'Show recent changes.',
        example => '#recent(10)',
    };
}

1;
