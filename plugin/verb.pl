use strict;

package verb;

sub plugin_inline {
    my ($escaped_argument) = @_;
    return qq(<span class="verb">$escaped_argument</span>);
}

sub plugin_usage {
    return {
        name => 'verb',
        version => '1.0',
        author => 'Hiroshi Yuki <hyuki@hyuki.com>',
        syntax => '&verb(as-is string)',
        description => 'Inline verbatim (hard).',
        example => '&verb(ThisIsNotWikiName)',
    };
}

1;
