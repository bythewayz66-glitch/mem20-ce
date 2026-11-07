package Mem20CE;
use strict;
use warnings;

our $VERSION = '0.1.0';

# Minimal Perl client skeleton for mem20-ce (Apache-2.0).

sub new {
    my ($class, %args) = @_;
    my $self = {
        store_path => $args{store_path} // "$ENV{HOME}/.mem20-ce/store",
    };
    return bless $self, $class;
}

sub remember {
    my ($self, $content, %opts) = @_;
    die "Wire to mem20-ce CLI or HTTP in next increment\n";
}

sub recall {
    my ($self, $query, %opts) = @_;
    die "Wire to mem20-ce CLI or HTTP in next increment\n";
}

sub contamination {
    my ($self) = @_;
    die "Wire to mem20-ce CLI or HTTP in next increment\n";
}

1;
