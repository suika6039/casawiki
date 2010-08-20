#this perl module for using Cassandra DB on YukiWiki 
package Cassandra::Cass4YukiWiki;

use strict;
use warnings;

use lib './Cassandra/lib';
use Cassandra::Cassandra;
use Cassandra::Constants;
use Cassandra::Types;

use Thrift;
use Thrift::BinaryProtocol;
use Thrift::Socket;
use Thrift::BufferedTransport;
use Thrift::FramedTransport;

sub TIEHASH
{
	my ($_pkg,$_host,$_port,$_ksp,$_cf,$_row) = @_;

	my $self;

	$self->{_socket} = new Thrift::Socket($_host,$_port);
	#$self->{_transport} = new Thrift::FramedTransport($self->{_socket},1024,1024);
	$self->{_transport} = new Thrift::BufferedTransport($self->{_socket},1024,1024);
	$self->{_protocol} = new Thrift::BinaryProtocol($self->{_transport});
	$self->{_client} = new Cassandra::CassandraClient($self->{_protocol});
	$self->{_keyspace} = $_ksp;
	$self->{_columnfamily} = $_cf;
	$self->{_row} = $_row;
	$self->{_consistency_level} = Cassandra::ConsistencyLevel::ONE;

	$self->{_transport}->open();

	return bless $self,$_pkg;
}

sub FETCH
{
	my $self = shift;
	my $column = shift;
	my $client = $self->{_client};
	my $column_path = new Cassandra::ColumnPath();
	$column_path->{column_family} = $self->{_columnfamily};
	$column_path->{super_column} = undef;
	$column_path->{column} = $column;
	
	my $value;
	eval{
		$value = $client->get($self->{_keyspace},$self->{_row},$column_path,$self->{_consistency_level});
	};
	if($@){
		return undef;
	}
	
	return $value->{column}->{value};
}

sub EXIST
{
	my $self = shift;
	my $column = shift;
	my $client = $self->{_client};
	my $column_path = new Cassandra::ColumnPath();
	$column_path->{column_family} = $self->{_columnfamily};
	$column_path->{super_column} = undef;
	$column_path->{column} = $column;
	
	my $value;
	eval{
		$value = $client->get($self->{_keyspace},$self->{_row},$column_path,$self->{_consistency_level});
	};
	if($@){
		return 0;
	}
	
	return 1;
}

sub STORE
{
	my ($_self,$_column,$_value) = @_;

	my $column_path = new Cassandra::ColumnPath();
	$column_path->{column_family} = $_self->{_columnfamily};
	$column_path->{super_column} = undef;
	$column_path->{column} = $_column;

	my $client = $_self->{_client};

	$client->insert($_self->{_keyspace},$_self->{_row},$column_path,$_value,time,$_self->{_consistency_level});
	
	return $_value;
}

sub DELETE
{
	my ($_self,$_column) = @_;
	my $client = $_self->{_client};
	
	my $column_path = new Cassandra::ColumnPath();
	$column_path->{column_family} = $_self->{_columnfamily};
	$column_path->{super_column} = undef;
	$column_path->{column} = $_column;

	$client->remove($_self->{_keyspace},$_self->{_row},$column_path,time,$_self->{_consistency_level});	
	
	return undef;
}

sub FIRSTKEY
{
	my ($_self) = @_;	

	my $client = $_self->{_client};

	my $column_parent = new Cassandra::ColumnParent();
	$column_parent->{column_family} = $_self->{_columnfamily};
	$column_parent->{super_column} = undef;
	
	my $slice_range = new Cassandra::SliceRange();
	$slice_range->{start} = "";
	$slice_range->{finish} = "";

	my $predicate = new Cassandra::SlicePredicate();
	my @list = $predicate->{column_names};
	$predicate->{slice_range} = $slice_range;

	my @result = $client->get_slice($_self->{_keyspace},$_self->{_row},$column_parent,$predicate,$_self->{_consistency_level});
	$_self->{_column_list} = $result[0];

	my $first_column = shift @{$_self->{_column_list}};	

	return $first_column->{column}->{name};
}

sub NEXTKEY
{
	my $_self = shift;
	my $next_item = shift @{$_self->{_column_list}};
	return $next_item->{column}->{name};
}

sub DESTROY
{
	my $self = shift;
	$self->{_transport}->close();
	return 1;
}

1;
