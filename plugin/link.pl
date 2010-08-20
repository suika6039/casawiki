use strict;

package link;

sub plugin_inline {
    my ($escaped_argument) = @_;
    my ($caption, $url) = split(/,/, $escaped_argument);
    if ($url =~ /^(mailto|http|https|ftp):/) {
        return qq(<a href="$url">$caption</a>);
    } else {
        return qq(&link($escaped_argument));
    }
}

sub plugin_usage {
    return {
        name => 'link',
        version => '1.1',
        author => 'Hiroshi Yuki <hyuki@hyuki.com>',
        syntax => '&link(caption,url)',
        description => 'Create link with given caption..',
        example => "Please visit &link(Hiroshi Yuki,http://www.hyuki.com/).",
    };
}

1;
