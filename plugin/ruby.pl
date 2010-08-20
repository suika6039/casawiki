use strict;

package ruby;

sub plugin_inline {
    my ($escaped_argument) = @_;
    my ($string,$ruby) = split(/,/, $escaped_argument);
    return qq(<ruby><rb>$string</rb><rp>(</rp><rt>$ruby</rt><rp>)</rp></ruby>);
}

sub plugin_usage {
    return {
        name => 'ruby',
        version => '1.0',
        author => 'Hiroshi Yuki <hyuki@hyuki.com>',
        syntax => '&ruby(string,ruby)',
        description => 'Make ruby.',
        example => '&ruby(KANJI,kana)',
    };
}

1;
