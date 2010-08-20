#!/usr/bin/perl -
#
# wiki.cgi - CasaWiki , YukiWiki on Cassandra
#
# suika6039
#
##############################
#
# wiki.cgi - This is YukiWiki, yet another Wiki clone.
#
# Copyright (C) 2000-2004 by Hiroshi Yuki.
# <hyuki@hyuki.com>
# http://www.hyuki.com/yukiwiki/
#
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.
#
##############################
# Libraries.
use strict;
use lib qw(.);
use CGI qw(:standard);
use CGI::Carp qw(fatalsToBrowser);
use Yuki::RSS;
use Yuki::DiffText qw(difftext);
use Yuki::YukiWikiDB;
use Yuki::PluginManager;
use Cassandra::Cass4YukiWiki;
use Fcntl;

# Check if the server can use 'AnyDBM_File' or not.
# eval 'use AnyDBM_File';
# my $error_AnyDBM_File = $@;
my $version = '10.0819';
##############################
#
# You MUST modify following '$modifier_...' variables.
#
my $modifier_mail = 'casawiki@localhost';
my $modifier_url = 'http://localhost/casawiki/';
my $modifier_name = 'casawiki user';
my $modifier_dir_data = '.'; # Your data directory (not URL, but DIRECTORY).
my $modifier_url_data = '.'; # Your data URL (not DIRECTORY, but URL).
my $modifier_rss_title = "CasaWiki $version";
my $modifier_rss_link = 'http://localhost/casawiki/wiki.cgi';
my $modifier_rss_about = 'http://localhost/casawiki/wiki.cgi?RssPage';
my $modifier_rss_description = 'This is CasaWiki, yet another Wiki clone';
my $modifier_rss_timezone = '+09:00';
##############################
#
# You MAY modify following variables.
#
#my $modifier_dbtype = 'YukiWikiDB';
my $modifier_dbtype = 'Cass4YukiWiki';
my $modifier_sendmail = '';
# my $modifier_sendmail = '/usr/sbin/sendmail -t -n';
my $modifier_dir_plugin = './plugin';
##############################
#
# You MAY modify following variables.
#
my $file_touch = "$modifier_dir_data/touched.txt";
my $file_resource = "$modifier_dir_data/resource.txt";
my $file_FrontPage = "$modifier_dir_data/frontpage.txt";
my $file_conflict = "$modifier_dir_data/conflict.txt";
my $file_format = "$modifier_dir_data/format.txt";
my $file_rss = "$modifier_dir_data/wiki.cgi?RssPage";
my $url_cgi = 'wiki.cgi';
my $url_stylesheet = "$modifier_url_data/wiki.css";
my $icontag = qq(<img src="$modifier_url_data/icon40x40.gif" alt="*" width="40" height="40" />);
my $maxrecent = 50;
my $max_message_length = 500_000; # -1 for unlimited.
my $cols = 80;
my $rows = 20;
##############################
#
# You MAY modify following variables.
# 
my $dataname = "$modifier_dir_data/wiki";
my $infoname = "$modifier_dir_data/info";
my $diffname = "$modifier_dir_data/diff";
my $editchar = '?';
my $subject_delimiter = ' - ';
my $use_autoimg = 1; # automatically convert image URL into <img> tag.
my $use_exists = 0; # If you can use 'exists' method for your DB.
my $use_FixedFrontPage = 0;
##############################
my $InterWikiName = 'InterWikiName';
my $RecentChanges = 'RecentChanges';
my $AdminChangePassword = 'AdminChangePassword';
my $CompletedSuccessfully = 'CompletedSuccessfully';
my $FrontPage = 'FrontPage';
my $IndexPage = 'IndexPage';
my $SearchPage = 'SearchPage';
my $CreatePage = 'CreatePage';
my $ErrorPage = 'ErrorPage';
my $RssPage = 'RssPage';
my $AdminSpecialPage = 'Admin Special Page'; # must include spaces.
##############################
my $wiki_name = '\b([A-Z][a-z]+([A-Z][a-z]+)+)\b';
my $bracket_name = '\[\[(\S+?)\]\]';
my $embedded_name = '\[\[(#\S+?)\]\]';
my $interwiki_definition = '\[\[(\S+?)\ (\S+?)\]\]';
my $interwiki_name = '([^:]+):([^:].*)';
# Sorry for wierd regex.
my $inline_plugin = '\&amp;(\w+)\((([^()]*(\([^()]*\))?)*)\)';
##############################
my $embed_comment = '[[#comment]]';
my $embed_rcomment = '[[#rcomment]]';
##############################
my $info_ConflictChecker = 'ConflictChecker';
my $info_LastModified = 'LastModified';
my $info_IsFrozen = 'IsFrozen';
my $info_AdminPassword = 'AdminPassword';
##############################
my $kanjicode = 'euc';
my $charset = 'UTF-8';
my $lang = 'ja';
my %fixedpage = (
    $IndexPage => 1,
    $CreatePage => 1,
    $ErrorPage => 1,
    $RssPage => 1,
    $RecentChanges => 1,
    $SearchPage => 1,
    $AdminChangePassword => 1,
    $CompletedSuccessfully => 1,
    $FrontPage => $use_FixedFrontPage,
);
my %form;
my %database;
my %infobase;
my %diffbase;
my %resource;
my %interwiki;
my $plugin_manager;
my $plugin_context = {
    debug => 0,
    database => \%database,
    infobase => \%infobase,
    resource => \%resource,
    form => \%form,
    interwiki => \%interwiki,
    url_cgi => $url_cgi,
};
##############################
my %page_command = (
    $IndexPage => 'index',
    $SearchPage => 'searchform',
    $CreatePage => 'create',
    $RssPage => 'rss',
    $AdminChangePassword => 'adminchangepasswordform',
    $FrontPage => 'FrontPage',
);
my %command_do = (
    read => \&do_read,
    edit => \&do_edit,
    adminedit => \&do_adminedit,
    adminchangepasswordform => \&do_adminchangepasswordform,
    adminchangepassword => \&do_adminchangepassword,
    write => \&do_write,
    index => \&do_index,
    searchform => \&do_searchform,
    search => \&do_search,
    create => \&do_create,
    createresult => \&do_createresult,
    FrontPage => \&do_FrontPage,
    comment => \&do_comment,
    rss => \&do_rss,
    diff => \&do_diff,
);
##############################
# &test_convert;
&main;
exit(0);
##############################

sub main {
    &init_resource;
    # &check_modifiers;
    &open_db;
    &init_form;
    &init_InterWikiName;
    &init_plugin;
    if ($command_do{$form{mycmd}}) {
        &{$command_do{$form{mycmd}}};
    } else {
        &do_FrontPage;
    }
    &close_db;
}

sub do_read {
    &print_header($form{mypage});
    &print_content($database{$form{mypage}});
    &print_footer($form{mypage});
}

sub do_edit {
    my ($page) = &unarmor_name(&armor_name($form{mypage}));
    &print_header($page);
    if (not &is_editable($page)) {
        &print_message($resource{cantchange});
    } elsif (&is_frozen($page)) {
        &print_message($resource{cantchange});
    } else {
        &print_editform($database{$page}, &get_info($page, $info_ConflictChecker), admin=>0);
    }
    &print_footer($page);
}

sub do_adminedit {
    my ($page) = &unarmor_name(&armor_name($form{mypage}));
    &print_header($page);
    if (not &is_editable($page)) {
        &print_message($resource{cantchange});
    } else {
        &print_message($resource{passwordneeded});
        &print_editform($database{$page}, &get_info($page, $info_ConflictChecker), admin=>1);
    }
    &print_footer($page);
}

sub do_adminchangepasswordform {
    &print_header($AdminChangePassword);
    &print_passwordform;
    &print_footer($AdminChangePassword);
}

sub do_adminchangepassword {
    if ($form{mynewpassword} ne $form{mynewpassword2}) {
        &print_error($resource{passwordmismatcherror});
    }
    my ($validpassword_crypt) = &get_info($AdminSpecialPage, $info_AdminPassword);
    if ($validpassword_crypt) {
        if (not &valid_password($form{myoldpassword})) {
            &send_mail_to_admin(<<"EOD", "AdminChangePassword");
myoldpassword=$form{myoldpassword}
mynewpassword=$form{mynewpassword}
mynewpassword2=$form{mynewpassword2}
EOD
            &print_error($resource{passworderror});
        }
    }
    my ($sec, $min, $hour, $day, $mon, $year, $weekday) = localtime(time);
    my (@token) = ('0'..'9', 'A'..'Z', 'a'..'z');
    my $salt1 = $token[(time | $$) % scalar(@token)];
    my $salt2 = $token[($sec + $min*60 + $hour*60*60) % scalar(@token)];
    my $crypted = crypt($form{mynewpassword}, "$salt1$salt2");
    &set_info($AdminSpecialPage, $info_AdminPassword, $crypted);

    &print_header($CompletedSuccessfully);
    &print_message($resource{passwordchanged});
    &print_footer($CompletedSuccessfully);
}

sub do_index {
    &print_header($IndexPage);
    print qq(<ul>);
    foreach my $page (sort keys %database) {
        if (&is_editable($page)) {
            print qq(<li><a href="$url_cgi?@{[&encode($page)]}">@{[&escape($page)]}</a>@{[&escape(&get_subjectline($page))]}</li>);
            # print qq(<li>@{[&get_info($page, $info_IsFrozen)]}</li>);
            # print qq(<li>@{[0 + &is_frozen($page)]}</li>);
        }
    }
    print qq(</ul>);
    &print_footer($IndexPage);
}

sub do_write {
    if (&keyword_reject()) {
        return;
    }

    if (&frozen_reject()) {
        return;
    }

    if (&length_reject()) {
        return;
    }

    if (not &is_editable($form{mypage})) {
        &print_header($form{mypage});
        &print_message($resource{cantchange});
        &print_footer($form{mypage});
        return;
    }

    if (&conflict($form{mypage}, $form{mymsg})) {
        return;
    }

    # Making diff
    if (1) {
        &open_diff;
        my @msg1 = split(/\r?\n/, $database{$form{mypage}});
        my @msg2 = split(/\r?\n/, $form{mymsg});
        $diffbase{$form{mypage}} = &difftext(\@msg1, \@msg2);
        &close_diff;
    }

    if ($form{mymsg}) {
        $database{$form{mypage}} = $form{mymsg};
        &send_mail_to_admin($form{mypage}, "Modify");
        &set_info($form{mypage}, $info_ConflictChecker, '' . localtime);
        if ($form{mytouch}) {
            &set_info($form{mypage}, $info_LastModified, '' . localtime);
            &update_recent_changes;
        }
        &set_info($form{mypage}, $info_IsFrozen, 0 + $form{myfrozen});
        &print_header($CompletedSuccessfully);
        &print_message($resource{saved});
        &print_content("$resource{continuereading} @{[&armor_name($form{mypage})]}");
        &print_footer($CompletedSuccessfully);
    } else {
        &send_mail_to_admin($form{mypage}, "Delete");
        delete $database{$form{mypage}};
        delete $infobase{$form{mypage}};
        if ($form{mytouch}) {
            &update_recent_changes;
        }
        &print_header($form{mypage});
        &print_message($resource{deleted});
        &print_footer($form{mypage});
    }
}

sub do_searchform {
    &print_header($SearchPage);
    &print_searchform("");
    &print_footer($SearchPage);
}

sub do_search {
    my $word = &escape($form{mymsg});
    &print_header($SearchPage);
    &print_searchform($word);
    my $counter = 0;
    foreach my $page (sort keys %database) {
        next if $page =~ /^$RecentChanges$/;
        if ($database{$page} =~ /\Q$form{mymsg}\E/ or $page =~ /\Q$form{mymsg}\E/) {
            if ($counter == 0) {
                print qq|<ul>|;
            }
            print qq(<li><a href ="$url_cgi?@{[&encode($page)]}">@{[&escape($page)]}</a>@{[&escape(&get_subjectline($page))]}</li>);
            $counter++;
        }
    }
    if ($counter == 0) {
        &print_message($resource{notfound});
    } else {
        print qq|</ul>|;
    }
    &print_footer($SearchPage);
}

sub do_create {
    &print_header($CreatePage);
    print <<"EOD";
<form action="$url_cgi" method="post">
    <input type="hidden" name="mycmd" value="edit">
    <strong>$resource{newpagename}</strong><br>
    <input type="text" name="mypage" value="" size="20">
    <input type="submit" value="$resource{createbutton}"><br>
</form>
EOD
    &print_footer($CreatePage);
}

sub do_FrontPage {
    if ($fixedpage{$FrontPage}) {
        open(FILE, $file_FrontPage) or &print_error("($file_FrontPage)");
        my $content = join('', <FILE>);
        &code_convert(\$content, $kanjicode);
        close(FILE);
        &print_header($FrontPage);
        &print_content($content);
        &print_footer($FrontPage);
    } else {
        $form{mycmd} = 'read';
        $form{mypage} = $FrontPage;
        &do_read;
    }
}

sub print_error {
    my ($msg) = @_;
    &print_header($ErrorPage);
    print qq(<p><strong class="error">$msg</strong></p>);
    &print_plugin_log;
    &print_footer($ErrorPage);
    exit(0);
}

sub print_header {
    my ($page) = @_;
    my $bodyclass = "normal";
    my $editable = 0;
    my $admineditable = 0;
    if (&is_frozen($page) and $form{mycmd} =~ /^(read|write)$/) {
        $editable = 0;
        $admineditable = 1;
        $bodyclass = "frozen";
    } elsif (&is_editable($page) and $form{mycmd} =~ /^(read|write)$/) {
        $admineditable = 1;
        $editable = 1;
    } else {
        $editable = 0;
    }
    my $cookedpage = &encode($page);
    my $escapedpage = &escape($page);
    print <<"EOD";
Content-type: text/html; charset=$charset

<!DOCTYPE html
    PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
    "http://www.w3.org/TR/html4/loose.dtd">
<html lang="$lang">
<head>
    <meta http-equiv="Content-Language" content="$lang">
    <meta http-equiv="Content-Type" content="text/html; charset=$charset">
    <title>$escapedpage @{[&escape(&get_subjectline($page))]}</title>
    <link rel="index" href="$url_cgi?$IndexPage">
    <link rev="made" href="mailto:$modifier_mail">
    <link rel="stylesheet" type="text/css" href="$url_stylesheet">
    <link rel="alternate" type="application/rss+xml" title="RSS" href="$modifier_rss_about" />
</head>
<body class="$bodyclass">
<div class="tools">
    @{[ $admineditable
        ? qq(<a title="$resource{admineditthispage}" href="$url_cgi?mycmd=adminedit&amp;mypage=$cookedpage">$resource{admineditbutton}</a> | )
        : qq()
    ]}
    @{[ $editable
        ? qq(<a title="$resource{editthispage}" href="$url_cgi?mycmd=edit&amp;mypage=$cookedpage">$resource{editbutton}</a> | )
        : qq()
    ]}
    @{[ $admineditable
        ? qq(<a href="$url_cgi?mycmd=diff&amp;mypage=$cookedpage">$resource{diffbutton}</a> | )
        : qq()
    ]}
    <a href="$url_cgi?$CreatePage">$resource{createbutton}</a> | 
    <a href="$url_cgi?$IndexPage">$resource{indexbutton}</a> | 
    <a href="$modifier_rss_about">$resource{rssbutton}</a> | 
    <a href="$url_cgi?$FrontPage">$FrontPage</a> | 
    <a href="$url_cgi?$SearchPage">$resource{searchbutton}</a> | 
    <a href="$url_cgi?$RecentChanges">$resource{recentchangesbutton}</a>
</div>
<h1 class="header"><a
    title="$resource{searchthispage}"
    href="$url_cgi?mycmd=search&amp;mymsg=$cookedpage">@{[&escape($page)]}</a>@{[&escape(&get_subjectline($page))]}</h1>
EOD
}

sub print_footer {
    my ($page) = @_;
    print <<"EOD";
<hr>
<address class="footer">
    Powered by <a href="http://www.hyuki.com/yukiwiki/">CasaWiki</a> $version <br />
    Modified by <a href="$modifier_url">$modifier_name</a>.
</address>
<p class="footer">
   <!-- <a href="http://www.hyuki.com/yukiwiki/">$icontag</a> -->
</p>
</body>
</html>
EOD
}

sub escape {
    my $s = shift;
    $s =~ s|\r\n|\n|g;
    $s =~ s|\&|&amp;|g;
    $s =~ s|<|&lt;|g;
    $s =~ s|>|&gt;|g;
    $s =~ s|"|&quot;|g;
    return $s;
}

sub unescape {
    my $s = shift;
    # $s =~ s|\n|\r\n|g;
    $s =~ s|\&amp;|\&|g;
    $s =~ s|\&lt;|\<|g;
    $s =~ s|\&gt;|\>|g;
    $s =~ s|\&quot;|\"|g;
    return $s;
}

sub print_content {
    my ($rawcontent) = @_;
    print &text_to_html($rawcontent, toc=>1);
}

sub text_to_html {
    my ($txt, %option) = @_;
    my (@txt) = split(/\r?\n/, $txt);
    my (@toc);
    my $verbatim;
    my $tocnum = 0;
    my (@saved, @result);
    unshift(@saved, "</p>");
    push(@result, "<p>");
    foreach (@txt) {
        chomp;

        # verbatim.
        if ($verbatim->{func}) {
            if (/^\Q$verbatim->{done}\E$/) {
                undef $verbatim;
                push(@result, splice(@saved));
            } else {
                push(@result, $verbatim->{func}->($_));
            }
            next;
        }

        # non-verbatim follows.
        push(@result, shift(@saved)) if (@saved and $saved[0] eq '</pre>' and /^[^ \t]/);
        if (/^(\*{1,3})(.+)/) {
            # $hn = 'h2', 'h3' or 'h4'
            my $hn = "h" . (length($1) + 1);
            push(@toc, '-' x length($1) . qq( <a href="#i$tocnum">) . &remove_tag(&inline($2)) . qq(</a>\n));
            push(@result, splice(@saved), qq(<$hn><a name="i$tocnum"> </a>) . &inline($2) . qq(</$hn>));
            $tocnum++;
        } elsif (/^(-{2,3})\($/) {
            if ($& eq '--(') {
                $verbatim = { func => \&inline, done => '--)', class => 'verbatim-soft' };
            } else {
                $verbatim = { func => \&escape, done => '---)', class => 'verbatim-hard' };
            }
            &back_push('pre', 1, \@saved, \@result, " class='$verbatim->{class}'");
        } elsif (/^----/) {
            push(@result, splice(@saved), '<hr>');
        } elsif (/^(-{1,3})(.+)/) {
            &back_push('ul', length($1), \@saved, \@result);
            push(@result, '<li>' . &inline($2) . '</li>');
        } elsif (/^:([^:]+):(.+)/) {
            &back_push('dl', 1, \@saved, \@result);
            push(@result, '<dt>' . &inline($1) . '</dt>', '<dd>' . &inline($2) . '</dd>');
        } elsif (/^(>{1,3})(.+)/) {
            &back_push('blockquote', length($1), \@saved, \@result);
            push(@result, &inline($2));
        } elsif (/^$/) {
            push(@result, splice(@saved));
            unshift(@saved, "</p>");
            push(@result, "<p>");
        } elsif (/^(\s+.*)$/) {
            &back_push('pre', 1, \@saved, \@result);
            push(@result, &escape($1)); # Not &inline, but &escape
        } elsif (/^\,(.*?)[\x0D\x0A]*$/) {
            &back_push('table', 1, \@saved, \@result, ' border="1"');
            #######
            # This part is taken from Mr. Ohzaki's Perl Memo and Makio Tsukamoto's WalWiki.
            # XXXXX
            my $tmp = "$1,";
            my @value = map {/^"(.*)"$/ ? scalar($_ = $1, s/""/"/g, $_) : $_} ($tmp =~ /("[^"]*(?:""[^"]*)*"|[^,]*),/g);
            my @align = map {(s/^\s+//) ? ((s/\s+$//) ? ' align="center"' : ' align="right"') : ''} @value;
            my @colspan = map {($_ eq '==') ? 0 : 1} @value;
            for (my $i = 0; $i < @value; $i++) {
                if ($colspan[$i]) {
                    while ($i + $colspan[$i] < @value and $value[$i + $colspan[$i]] eq '==') {
                        $colspan[$i]++;
                    }
                    $colspan[$i] = ($colspan[$i] > 1) ? sprintf(' colspan="%d"', $colspan[$i]) : '';
                    $value[$i] = sprintf('<td%s%s>%s</td>', $align[$i], $colspan[$i], &inline($value[$i]));
                } else {
                    $value[$i] = '';
                }
            }
            push(@result, join('', '<tr>', @value, '</tr>'));
            # XXXXX
            #######
        } elsif (/^\#(\w+)(\((.*)\))?/) {
            # BlockPlugin.
            my $original_line = $_;
            my $plugin_name = $1;
            my $argument = &escape($3);
            my $result = $plugin_manager->call($plugin_name, 'block', $argument);
            if (defined($result)) {
                push(@result, splice(@saved));
            } else {
                $result = $original_line;
            }
            push(@result, $result);
        } else {
            push(@result, &inline($_));
        }
    }
    push(@result, splice(@saved));

    if ($option{toc}) {
        # Convert @toc (table of contents) to HTML.
        # This part is taken from Makio Tsukamoto's WalWiki.
        my (@tocsaved, @tocresult);
        foreach (@toc) {
            if (/^(-{1,3})(.*)/) {
                &back_push('ul', length($1), \@tocsaved, \@tocresult);
                push(@tocresult, '<li>' . $2 . '</li>');
            }
        }
        push(@tocresult, splice(@tocsaved));

        # Insert "table of contents".
        if (@tocresult) {
            unshift(@tocresult, qq(<h2>$resource{table_of_contents}</h2>));
        }

        return join("\n", @tocresult, @result);
    } else {
        return join("\n", @result);
    }
}

sub back_push {
    my ($tag, $level, $savedref, $resultref, $attr) = @_;
    while (@$savedref > $level) {
        push(@$resultref, shift(@$savedref));
    }
    if ($savedref->[0] ne "</$tag>") {
        push(@$resultref, splice(@$savedref));
    }
    while (@$savedref < $level) {
        unshift(@$savedref, "</$tag>");
        push(@$resultref, "<$tag$attr>");
    }
}

sub remove_tag {
    my ($line) = @_;
    $line =~ s|\<\/?[A-Za-z][^>]*?\>||g;
    return $line;
}

sub inline {
    my ($line) = @_;
    $line = &escape($line);
    $line =~ s|'''([^']+?)'''|<i>$1</i>|g;  # Italic
    $line =~ s|''([^']+?)''|<b>$1</b>|g;    # Bold
    $line =~ s|(\d\d\d\d-\d\d-\d\d \(\w\w\w\) \d\d:\d\d:\d\d)|<span class="date">$1</span>|g;   # Date
    $line =~ s!
                (
                    ((mailto|http|https|ftp):([^\x00-\x20()<>\x7F-\xFF])*)  # Direct http://...
                        |
                    ($bracket_name)             # [[likethis]], [[#comment]], [[Friend:remotelink]]
                        |
                    ($interwiki_definition)     # [[Friend http://somewhere/?q=sjis($1)]]
                        |
                    ($wiki_name)                # LocalLinkLikeThis
                        |
                    ($inline_plugin)            # &user_defined_plugin(123,hello)
                )
            !
                &make_link($1)
            !gex;
    return $line;
}

sub make_link {
    my $chunk = shift;
    if ($chunk =~ /^(http|https|ftp):/) {
        if ($use_autoimg and $chunk =~ /\.(gif|png|jpeg|jpg)$/) {
            return qq(<a href="$chunk"><img src="$chunk"></a>);
        } else {
            return qq(<a href="$chunk">$chunk</a>);
        }
    } elsif ($chunk =~ /^(mailto):(.*)/) {
        return qq(<a href="$chunk">$2</a>);
    } elsif ($chunk =~ /^$interwiki_definition$/) {
        return qq(<span class="InterWiki">$chunk</span>);
    } elsif ($chunk =~ /^$embedded_name$/) {
        return &embedded_to_html($chunk);
    } elsif ($chunk =~ /^$inline_plugin$/) {
        # InlinePlugin.
        my $plugin_name = $1;
        my $argument = $2;
        my $result = $plugin_manager->call($plugin_name, 'inline', $argument);
        if (defined($result)) {
            return $result;
        } else {
            return $chunk;
        }
    } else {
        $chunk = &unarmor_name($chunk);
        $chunk = &unescape($chunk); # To treat '&' or '>' or '<' correctly.
        my $cookedchunk = &encode($chunk);
        my $escapedchunk = &escape($chunk);
        if ($chunk =~ /^$interwiki_name$/) {
            my ($intername, $localname) = ($1, $2);
            my $remoteurl = $interwiki{$intername};
            if ($remoteurl =~ /^(http|https|ftp):\/\//) { # Check if scheme if valid.
                $remoteurl =~ s/\b(euc|sjis|ykwk|asis)\(\$1\)/&interwiki_convert($1, $localname)/e;
                return qq(<a href="$remoteurl">$escapedchunk</a>);
            } else {
                return $escapedchunk;
            }
        } elsif ($database{$chunk}) {
            my $subject = &escape(&get_subjectline($chunk, delimiter => ''));
            return qq(<a title="$subject" href="$url_cgi?$cookedchunk">$escapedchunk</a>);
        } elsif ($page_command{$chunk}) {
            return qq(<a title="$escapedchunk" href="$url_cgi?$cookedchunk">$escapedchunk</a>);
        } else {
            return qq($escapedchunk<a title="$resource{editthispage}" class="editlink" href="$url_cgi?mycmd=edit&amp;mypage=$cookedchunk">$editchar</a>);
        }
    }
}

sub print_message {
    my ($msg) = @_;
    print qq(<p><strong>$msg</strong></p>);
}

sub init_form {
    if (param()) {
        foreach my $var (param()) {
            $form{$var} = param($var);
        }
    } else {
        $ENV{QUERY_STRING} = $FrontPage;
    }

    my $query = &decode($ENV{QUERY_STRING});
    if ($page_command{$query}) {
        $form{mycmd} = $page_command{$query};
        $form{mypage} = $query;
    } elsif ($query =~ /^($wiki_name)$/) {
        $form{mycmd} = 'read';
        $form{mypage} = $1;
    } elsif ($database{$query}) {
        $form{mycmd} = 'read';
        $form{mypage} = $query;
    }

    # mypreview_edit        -> do_edit, with preview.
    # mypreview_adminedit   -> do_adminedit, with preview.
    # mypreview_write       -> do_write, without preview.
    foreach (keys %form) {
        if (/^mypreview_(.*)$/) {
            $form{mycmd} = $1;
            $form{mypreview} = 1;
        }
    }

    #
    # $form{mycmd} is frozen here.
    #

    $form{mymsg} = &code_convert(\$form{mymsg}, $kanjicode);
    $form{myname} = &code_convert(\$form{myname}, $kanjicode);
}

sub update_recent_changes {
    my $update = "- @{[&get_now]} @{[&armor_name($form{mypage})]} @{[&get_subjectline($form{mypage})]}";
    my @oldupdates = split(/\r?\n/, $database{$RecentChanges});
    my @updates;
    foreach (@oldupdates) {
        /^\- \d\d\d\d\-\d\d\-\d\d \(...\) \d\d:\d\d:\d\d (\S+)/;    # date format.
        my $name = &unarmor_name($1);
        if (&is_exist_page($name) and ($name ne $form{mypage})) {
            push(@updates, $_);
        }
    }
    if (&is_exist_page($form{mypage})) {
        unshift(@updates, $update);
    }
    splice(@updates, $maxrecent + 1);
    $database{$RecentChanges} = join("\n", @updates);
    if ($file_touch) {
        open(FILE, "> $file_touch");
        print FILE localtime() . "\n";
        close(FILE);
    }
    if ($file_rss) {
        #&update_rssfile;
    }
}

sub get_subjectline {
    my ($page, %option) = @_;
    if (not &is_editable($page)) {
        return "";
    } else {
        # Delimiter check.
        my $delim = $subject_delimiter;
        if (defined($option{delimiter})) {
            $delim = $option{delimiter};
        }

        # Get the subject of the page.
        my $subject = $database{$page};
        $subject =~ s/\r?\n.*//s;
        return "$delim$subject";
    }
}

sub send_mail_to_admin {
#    my ($page, $mode) = @_;
#    return unless $modifier_sendmail;
#    my $message = <<"EOD";
#To: $modifier_mail
#From: $modifier_mail
#Subject: [Wiki/$mode]
#MIME-Version: 1.0
#Content-Type: text/plain; charset=ISO-2022-JP
#Content-Transfer-Encoding: 7bit
#
#--------
#MODE = $mode
#REMOTE_ADDR = $ENV{REMOTE_ADDR}
#REMOTE_HOST = $ENV{REMOTE_HOST}
#--------
#$page
#--------
#$database{$page}
#--------
#EOD
#    &code_convert(\$message, 'jis');
#    open(MAIL, "| $modifier_sendmail");
#    print MAIL $message;
#    close(MAIL);
}

sub open_db {
    if ($modifier_dbtype eq 'dbmopen') {
        dbmopen(%database, $dataname, 0666) or &print_error("(dbmopen) $dataname");
        dbmopen(%infobase, $infoname, 0666) or &print_error("(dbmopen) $infoname");
    } elsif ($modifier_dbtype eq 'AnyDBM_File') {
        tie(%database, "AnyDBM_File", $dataname, O_RDWR|O_CREAT, 0666) or &print_error("(tie AnyDBM_File) $dataname");
        tie(%infobase, "AnyDBM_File", $infoname, O_RDWR|O_CREAT, 0666) or &print_error("(tie AnyDBM_File) $infoname");
    } elsif ($modifier_dbtype eq 'Cass4YukiWiki') {
		tie(%database,"Cassandra::Cass4YukiWiki","localhost",9160,"YukiWikiKS","YukiWikiCF","database") or &print_error("(tie Cassandra::Cass4YukiWiki) $dataname");
		tie(%infobase,"Cassandra::Cass4YukiWiki","localhost",9160,"YukiWikiKS","YukiWikiCF","infobase") or &print_error("(tie Cassandra::Cass4YukiWiki) $infoname");
    } else {
        tie(%database, "Yuki::YukiWikiDB", $dataname) or &print_error("(tie Yuki::YukiWikiDB) $dataname");
        tie(%infobase, "Yuki::YukiWikiDB", $infoname) or &print_error("(tie Yuki::YukiWikiDB) $infoname");
    }
}

sub close_db {
    if ($modifier_dbtype eq 'dbmopen') {
        dbmclose(%database);
        dbmclose(%infobase);
    } elsif ($modifier_dbtype eq 'AnyDBM_File') {
        untie(%database);
        untie(%infobase);
    } elsif ($modifier_dbtype eq 'Cass4YukiWiki') {
        untie(%database);
        untie(%infobase);
    } else {
        untie(%database);
        untie(%infobase);
    }
}

sub open_diff {
    if ($modifier_dbtype eq 'dbmopen') {
        dbmopen(%diffbase, $diffname, 0666) or &print_error("(dbmopen) $diffname");
    } elsif ($modifier_dbtype eq 'AnyDBM_File') {
        tie(%diffbase, "AnyDBM_File", $diffname, O_RDWR|O_CREAT, 0666) or &print_error("(tie AnyDBM_File) $diffname");
    } elsif ($modifier_dbtype eq 'Cass4YukiWiki') {
		tie(%diffbase,"Cassandra::Cass4YukiWiki","localhost",9160,"YukiWikiKS","YukiWikiCF","diffbase") or &print_error("(tie Cassandra::Cass4YukiWiki) $infoname");
    } else {
        tie(%diffbase, "Yuki::YukiWikiDB", $diffname) or &print_error("(tie Yuki::YukiWikiDB) $diffname");
    }
}

sub close_diff {
    if ($modifier_dbtype eq 'dbmopen') {
        dbmclose(%diffbase);
    } elsif ($modifier_dbtype eq 'AnyDBM_File') {
        untie(%diffbase);
    } elsif ($modifier_dbtype eq 'Cass4YukiWiki') {
        untie(%diffbase);
    } else {
        untie(%diffbase);
    }
}

sub print_searchform {
    my ($word) = @_;
    print <<"EOD";
<form action="$url_cgi" method="get">
    <input type="hidden" name="mycmd" value="search">
    <input type="text" name="mymsg" value="$word" size="20">
    <input type="submit" value="$resource{searchbutton}">
</form>
EOD
}

sub print_editform {
    my ($mymsg, $conflictchecker, %mode) = @_;
    my $frozen = &is_frozen($form{mypage});

    if ($form{mypreview}) {
        if ($form{mymsg}) {
            unless ($mode{conflict}) {
                print qq(<h3>$resource{previewtitle}</h3>\n);
                print qq($resource{previewnotice}\n);
                print qq(<div class="preview">\n);
                &print_content($form{mymsg});
                print qq(</div>\n);
            }
        } else {
            print qq($resource{previewempty});
        }
        $mymsg = &escape($form{mymsg});
    } else {
        $mymsg = &escape($mymsg);
    }

    my $edit = $mode{admin} ? 'adminedit' : 'edit';
    my $escapedmypage = &escape($form{mypage});
    my $escapedmypassword = &escape($form{mypassword});

    print <<"EOD";
<form action="$url_cgi" method="post">
    @{[ $mode{admin} ? qq($resource{frozenpassword} <input type="password" name="mypassword" value="$escapedmypassword" size="10"><br>) : "" ]}
    <input type="hidden" name="myConflictChecker" value="$conflictchecker">
    <input type="hidden" name="mypage" value="$escapedmypage">
    <textarea cols="$cols" rows="$rows" name="mymsg">
$mymsg</textarea><br>
@{[
    $mode{admin} ?
    qq(
    <input type="radio" name="myfrozen" value="1" @{[$frozen ? qq(checked="checked") : ""]}>$resource{frozenbutton}
    <input type="radio" name="myfrozen" value="0" @{[$frozen ? "" : qq(checked="checked")]}>$resource{notfrozenbutton}<br>)
    : ""
]}
@{[
    $mode{conflict} ? "" :
    qq(
        <input type="checkbox" name="mytouch" value="on" checked="checked">$resource{touch}<br>
        <input type="submit" name="mypreview_$edit" value="$resource{previewbutton}">
        <input type="submit" name="mypreview_write" value="$resource{savebutton}"><br>
    )
]}
</form>
EOD
    unless ($mode{conflict}) {
        # Show the format rule.
        open(FILE, $file_format) or &print_error("($file_format)");
        my $content = join('', <FILE>);
        &code_convert(\$content, $kanjicode);
        close(FILE);
        print &text_to_html($content, toc=>0);
    }

    unless ($mode{conflict}) {
        # Show plugin information.
        my $plugin_usage = <<"EOD";
*$resource{available_plugins}
EOD
        foreach my $usage (@{$plugin_manager->usage}) {
            $plugin_usage .= <<"EOD";
** $usage->{name}
---(
$resource{plugin_usage_name}: $usage->{name}
$resource{plugin_usage_version}: $usage->{version}
$resource{plugin_usage_author}: $usage->{author}
$resource{plugin_usage_syntax}: $usage->{syntax}
$resource{plugin_usage_description}: $usage->{description}
$resource{plugin_usage_example}: $usage->{example}
---)
EOD
        }
        &code_convert(\$plugin_usage, $kanjicode);
        print &text_to_html($plugin_usage, toc=>0);
    }
}

sub print_passwordform {
        print <<"EOD";
<form action="$url_cgi" method="post">
    <input type="hidden" name="mycmd" value="adminchangepassword">
    $resource{oldpassword} <input type="password" name="myoldpassword" size="10"><br>
    $resource{newpassword} <input type="password" name="mynewpassword" size="10"><br>
    $resource{newpassword2} <input type="password" name="mynewpassword2" size="10"><br>
    <input type="submit" value="$resource{changepasswordbutton}"><br>
</form>
EOD
}

sub is_editable {
    my ($page) = @_;
    if (&is_bracket_name($page)) {
        return 0;
    } elsif ($fixedpage{$page}) {
        return 0;
    } elsif ($page =~ /\s/) {
        return 0;
    } elsif ($page =~ /^\#/) {
        return 0;
    } elsif ($page =~ /^$interwiki_name$/) {
        return 0;
    } elsif (not $page) {
        return 0;
    } else {
        return 1;
    }
}

# armor_name:
#   WikiName -> WikiName
#   not_wiki_name -> [[not_wiki_name]]
sub armor_name {
    my ($name) = @_;
    if ($name =~ /^$wiki_name$/) {
        return $name;
    } else {
        return "[[$name]]";
    }
}

# unarmor_name:
#   [[bracket_name]] -> bracket_name
#   WikiName -> WikiName
sub unarmor_name {
    my ($name) = @_;
    if ($name =~ /^$bracket_name$/) {
        return $1;
    } else {
        return $name;
    }
}

sub is_bracket_name {
    my ($name) = @_;
    if ($name =~ /^$bracket_name$/) {
        return 1;
    } else {
        return 0;
    }
}

sub decode {
    my ($s) = @_;
    $s =~ tr/+/ /;
    $s =~ s/%([A-Fa-f0-9][A-Fa-f0-9])/pack("C", hex($1))/eg;
    return $s;
}

# Thanks to WalWiki for [better encode].
sub encode {
    my ($encoded) = @_;
    $encoded =~ s/(\W)/'%' . unpack('H2', $1)/eg;
    return $encoded;
}

sub init_resource {
    open(FILE, $file_resource) or &print_error("(resource)");
    while (<FILE>) {
        chomp;
        next if /^#/;
        my ($key, $value) = split(/=/, $_, 2);
        $resource{$key} = &code_convert(\$value, $kanjicode);
    }
    close(FILE);
}

sub conflict {
    my ($page, $rawmsg) = @_;
    if ($form{myConflictChecker} eq &get_info($page, $info_ConflictChecker)) {
        return 0;
    }
    open(FILE, $file_conflict) or &print_error("(conflict)");
    my $content = join('', <FILE>);
    &code_convert(\$content, $kanjicode);
    close(FILE);
    &print_header($page);
    &print_content($content);
    &print_editform($rawmsg, $form{myConflictChecker}, frozen=>0, conflict=>1);
    &print_footer($page);
    return 1;
}

sub get_now {
    my (@week) = qw(Sun Mon Tue Wed Thu Fri Sat);
    my ($sec, $min, $hour, $day, $mon, $year, $weekday) = localtime(time);
    $year += 1900;
    $mon++;
    $mon = "0$mon" if $mon < 10;
    $day = "0$day" if $day < 10;
    $hour = "0$hour" if $hour < 10;
    $min = "0$min" if $min < 10;
    $sec = "0$sec" if $sec < 10;
    $weekday = $week[$weekday];
    return "$year-$mon-$day ($weekday) $hour:$min:$sec";
}

# [[YukiWiki http://www.hyuki.com/yukiwiki/wiki.cgi?euc($1)]]
sub init_InterWikiName {
    my $content = $database{$InterWikiName};
    while ($content =~ /\[\[(\S+) +(\S+)\]\]/g) {
        my ($name, $url) = ($1, $2);
        $interwiki{$name} = $url;
    }
}

sub interwiki_convert {
    my ($type, $localname) = @_;
    if ($type eq 'sjis' or $type eq 'euc') {
        &code_convert(\$localname, $type);
        return &encode($localname);
    } elsif ($type eq 'ykwk') {
        # for YukiWiki1
        if ($localname =~ /^$wiki_name$/) {
            return $localname;
        } else {
            &code_convert(\$localname, 'sjis');
            return &encode("[[" . $localname . "]]");
        }
    } elsif ($type eq 'asis') {
        return $localname;
    } else {
        return $localname;
    }
}

sub get_info {
    my ($page, $key) = @_;
    my %info = map { split(/=/, $_, 2) } split(/\n/, $infobase{$page});
    return $info{$key};
}

sub set_info {
    my ($page, $key, $value) = @_;
    my %info = map { split(/=/, $_, 2) } split(/\n/, $infobase{$page});
    $info{$key} = $value;
    my $s = '';
    for (keys %info) {
        $s .= "$_=$info{$_}\n";
    }
    $infobase{$page} = $s;
}

sub frozen_reject {
    my ($isfrozen) = &get_info($form{mypage}, $info_IsFrozen);
    my ($willbefrozen) = $form{myfrozen};
    if (not $isfrozen and not $willbefrozen) {
        # You need no check.
        return 0;
    } elsif (valid_password($form{mypassword})) {
        # You are admin.
        return 0;
    } else {
        &print_error($resource{passworderror});
        return 1;
    }
}

sub length_reject {
    if ($max_message_length < 0) {
        return 0;
    }
    if ($max_message_length < length($form{mymsg})) {
        &print_error($resource{toolongpost} . $max_message_length);
        return 1;
    }
    return 0;
}

sub valid_password {
    my ($givenpassword) = @_;
    my ($validpassword_crypt) = &get_info($AdminSpecialPage, $info_AdminPassword);
    if (crypt($givenpassword, $validpassword_crypt) eq $validpassword_crypt) {
        return 1;
    } else {
        return 0;
    }
}

sub is_frozen {
    my ($page) = @_;
    if (&get_info($page, $info_IsFrozen)) {
        return 1;
    } else {
        return 0;
    }
}

sub do_comment {
    my ($content) = $database{$form{mypage}};
    my $datestr = &get_now;
    my $namestr = $form{myname} ? " ''[[$form{myname}]]'' : " : " ";
    if ($content =~ s/(^|\n)(\Q$embed_comment\E)/$1- $datestr$namestr$form{mymsg}\n$2/) {
        ;
    } else {
        $content =~ s/(^|\n)(\Q$embed_rcomment\E)/$1$2\n- $datestr$namestr$form{mymsg}/;
    }
    if ($form{mymsg}) {
        $form{mymsg} = $content;
        $form{mytouch} = 'on';
        &do_write;
    } else {
        $form{mycmd} = 'read';
        &do_read;
    }
}

sub embedded_to_html {
    my ($embedded) = @_;
    my $escapedmypage = &escape($form{mypage});
    if ($embedded eq $embed_comment or $embedded eq $embed_rcomment) {
        my $conflictchecker = &get_info($form{mypage}, $info_ConflictChecker);
        return <<"EOD";
<form action="$url_cgi" method="post">
    <input type="hidden" name="mycmd" value="comment">
    <input type="hidden" name="mypage" value="$escapedmypage">
    <input type="hidden" name="myConflictChecker" value="$conflictchecker">
    <input type="hidden" name="mytouch" value="on">
    $resource{yourname}
    <input type="text" name="myname" value="" size="10">
    <input type="text" name="mymsg" value="" size="40">
    <input type="submit" value="$resource{commentbutton}">
</form>
EOD
    } else {
        return $embedded;
    }
}

sub code_convert {
    my ($contentref, $kanjicode) = @_;
	#&Jcode::convert($contentref, $kanjicode);       # for Jcode.pm
	#&jcode::convert($contentref, $kanjicode);       # for jcode.pl
    return $$contentref;
}

sub test_convert {
    my $txt = &text_to_html(<<"EOD", toc=>1);
*HEADER1
**HEADER1-1
-ITEM1
-ITEM2
-ITEM3
PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1
PAR1PAR1PAR1PAR1PAR1PAR1''BOLD''PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1
PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1

PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2
PAR2PAR2PAR2PAR2PAR2PAR2'''ITALIC'''PAR2PAR2PAR2PAR2PAR2PAR2PAR2
PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2
**HEADER1-2
:TERM1:DESCRIPTION1 AND ''BOLD''
PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1
PAR1PAR1PAR1PAR1PAR1PAR1''BOLD''PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1
PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1
:TERM2:DESCRIPTION2
:TERM3:DESCRIPTION3
----
*HEADER2
**HEADER2-1
http://www.hyuki.com/
**HEADER2-2

[[YukiWiki2]]

PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1
PAR1PAR1PAR1PAR1PAR1PAR1'''''BOLD ITALIC'''''PAR1PAR1PAR1PAR1PAR1
PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1PAR1
>PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2
>PAR2PAR2PAR2PAR2PAR2PAR2'''ITALIC'''PAR2PAR2PAR2PAR2PAR2PAR2PAR2
>PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2PAR2

LEVEL0LEVEL0LEVEL0LEVEL0LEVEL0LEVEL0LEVEL0

>LEVEL1
>LEVEL1
>LEVEL1
>>LEVEL2
>>LEVEL2
>>LEVEL2
>>>LEVEL3
-HELLO-1
--HELLO-2
(HELLO-2, HELLO-2, HELLO-2)
---HELLO-3
(HELLO-3, HELLO-3, HELLO-3)
--HELLO-2
---HELLO-3
--HELLO-2
---HELLO-3
>>>LEVEL3
>>>LEVEL3
>>>LEVEL3
>>>LEVEL3
EOD
    print $txt;
    exit;
}

sub do_diff {
    if (not &is_editable($form{mypage})) {
        &do_read;
        return;
    }
    &open_diff;
    my $title = $form{mypage};
    &print_header($title);
    $_ = &escape($diffbase{$form{mypage}});
    &close_diff;
    print qq(<h3>$resource{difftitle}</h3>);
    print qq($resource{diffnotice});
    print qq(<pre class="diff">);
    foreach (split(/\n/, $_)) {
        if (/^\+(.*)/) {
            print qq(<b class="added">$1</b>\n);
        } elsif (/^\-(.*)/) {
            print qq(<s class="deleted">$1</s>\n);
        } elsif (/^\=(.*)/) {
            print qq(<span class="same">$1</span>\n);
        } else {
            print qq|??? $_\n|;
        }
    }
    print qq(</pre>);
    print qq(<hr>);
    &print_footer($title);
}

sub do_rss {
	&print_rss;	
#    if ($file_rss) {
#        print <<"EOD";
#Status: 301 Moved Permanently
#Location: $modifier_rss_about
#
#EOD
#        return;
#    }
}

sub is_exist_page {
    my ($name) = @_;
    if ($use_exists) {
        return exists($database{$name});
    } else {
        return $database{$name};
    }
}

# sub check_modifiers {
#     if ($error_AnyDBM_File and $modifier_dbtype eq 'AnyDBM_File') {
#         &print_error($resource{anydbmfileerror});
#     }
# }

# Initialize plugins.
sub init_plugin {
    $plugin_manager = new Yuki::PluginManager($plugin_context, $modifier_dir_plugin);
}

sub print_plugin_log {
    if ($plugin_context->{debug}) {
        print "<pre>(print_plugin_log)\n", join("\n", @{$plugin_manager->{log}}), "</pre>";
    }
}

sub keyword_reject {
    my $s = $form{mymsg};
    my @reject_words = qw(
buy-cheap.com
ultram.online-buy.com
    );
    for (@reject_words) {
        if ($s =~ /\Q$_\E/) {
            &send_mail_to_admin($form{mypage}, "Rejectword: $_");
            sleep(30);
            return 1;
        }
    }
    return 0;
}

# Thanks to Makio Tsukamoto for dc_date.
sub print_rss {
    my $rss = new Yuki::RSS(
        version => '1.0',
        encoding => $charset,
    );
    $rss->channel(
        title => $modifier_rss_title,
        link  => $modifier_rss_link,
        about  => $modifier_rss_about,
        description => $modifier_rss_description,
    );
    my $recentchanges = $database{$RecentChanges};
    my $count = 0;
    foreach (split(/\n/, $recentchanges)) {
        last if ($count >= 15);
        /^\- (\d\d\d\d\-\d\d\-\d\d) \(...\) (\d\d:\d\d:\d\d) (\S+)/;    # date format.
        my $dc_date = "$1T$2$modifier_rss_timezone";
        my $title = &unarmor_name($3);
        my $escaped_title = &escape($title);
        my $link = $modifier_rss_link . '?' . &encode($title);
        my $description = $escaped_title . &escape(&get_subjectline($title));
        $rss->add_item(
            title => $escaped_title,
            link  => $link,
            description => $description,
            dc_date => $dc_date,
        );
        $count++;
    }
	print "Content-Type: application/rss+xml; charset=$charset\n\n";
    print $rss->as_string;
}

# Thanks to Makio Tsukamoto for dc_date.
sub update_rssfile {
    my $rss = new Yuki::RSS(
        version => '1.0',
        encoding => $charset,
    );
    $rss->channel(
        title => $modifier_rss_title,
        link  => $modifier_rss_link,
        about  => $modifier_rss_about,
        description => $modifier_rss_description,
    );
    my $recentchanges = $database{$RecentChanges};
    my $count = 0;
    foreach (split(/\n/, $recentchanges)) {
        last if ($count >= 15);
        /^\- (\d\d\d\d\-\d\d\-\d\d) \(...\) (\d\d:\d\d:\d\d) (\S+)/;    # date format.
        my $dc_date = "$1T$2$modifier_rss_timezone";
        my $title = &unarmor_name($3);
        my $escaped_title = &escape($title);
        my $link = $modifier_rss_link . '?' . &encode($title);
        my $description = $escaped_title . &escape(&get_subjectline($title));
        $rss->add_item(
            title => $escaped_title,
            link  => $link,
            description => $description,
            dc_date => $dc_date,
        );
        $count++;
    }
    open(FILE, "> $file_rss") or &print_error("($file_rss)");
    print FILE $rss->as_string;
    close(FILE);
}

1;
__END__
=head1 NAME

wiki.cgi - This is YukiWiki, yet another Wiki clone.

=head1 DESCRIPTION

YukiWiki is yet another Wiki clone.

YukiWiki can treat Japanese WikiNames (enclosed with [[ and ]]).
YukiWiki provides 'InterWiki' feature, RDF Site Summary (RSS),
and some embedded commands (such as [[#comment]] to add comments).

=head1 AUTHOR

Hiroshi Yuki <hyuki@hyuki.com> http://www.hyuki.com/yukiwiki/

=head1 LICENSE

Copyright (C) 2000-2006 by Hiroshi Yuki.

This program is free software; you can redistribute it and/or
modify it under the same terms as Perl itself.

=cut
