# Get available AZs for multi-AZ deployment
data "aws_availability_zones" "available" {
  state = "available"
}

# Main VPC for EKS cluster
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr_block

  tags = merge(
    var.resource_tags,
    {
      Name = "${var.project_prefix}-${title(terraform.workspace)}-vpc"
    }
  )
}

# Public subnets for load balancers and NAT gateway
resource "aws_subnet" "public" {
  count                   = var.subnet_count
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr_block, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(
    var.resource_tags,
    {
      Name = "${var.project_prefix}-${terraform.workspace}-public-${count.index + 1}"
    }
  )
}

# Private subnets for EKS worker nodes
resource "aws_subnet" "private" {
  count             = var.subnet_count
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr_block, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(
    var.resource_tags,
    {
      Name = "${var.project_prefix}-${terraform.workspace}-private-${count.index + 1}"
    }
  )
}

# Internet gateway for public subnet internet access
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_prefix}-${title(terraform.workspace)}-igw"
  }
}

# Route table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${var.project_prefix}-${title(terraform.workspace)}-rt"
  }
}

# Associate public subnets with public route table
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# EIP for NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"
  
  tags = merge(var.resource_tags, {
    Name = "${var.project_prefix}-${terraform.workspace}-nat-eip"
  })
  
  depends_on = [aws_internet_gateway.igw]
}

# Single NAT Gateway for cost optimization
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  
  tags = merge(var.resource_tags, {
    Name = "${var.project_prefix}-${terraform.workspace}-nat-gw"
  })
  
  depends_on = [
    aws_internet_gateway.igw,
    aws_route_table_association.public
  ]
}

# Private Route Tables
resource "aws_route_table" "private" {
  count  = length(aws_subnet.private)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = merge(var.resource_tags, {
    Name = "${var.project_prefix}-${terraform.workspace}-private-rt-${count.index + 1}"
  })
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}
