from . import bp

@bp.route('/users',methods=['POST'])
def create_user():
    """创建一个用户"""
    pass

@bp.route('/users',methods=['GET'])
def get_users():
    """返回所有用户的集合"""
    pass

@bp.route('/users/<int:id>',methods=['GET'])
def get_user(id):
    """获取单个用户"""
    pass

@bp.route('/users/<int:id>',methods=['PUT'])
def update_user(id):
    """修改单个用户"""
    pass

@bp.route('/users/<int:id>',methods=['DELETE'])
def delete_user(id):
    """修改单个用户"""
    pass