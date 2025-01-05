import java.util.*;

/**
* Red Black Tree Object
* Self balancing binary tree used to store keys and values
*
* @author David Lybeck
* @version 2023.11.07
*/
public class RedBlackTree<K extends Comparable<K>, V extends Comparable<V>> {
	/**
	 * Root node of Red Black Tree
	 */
    private Node root;

    /**
	* Constructor for the RedBlackTree type
	*/
    public RedBlackTree() {
        this.root = null;
    }

    /**
     * Adds a node to the RedBlackTree
     * 
     * @param key to node to be added
     * @param value of node to be added
     */
    public void put(K key, V value) {
    	Node newNode = new Node(key, value);
    	this.root = findAndAdd(this.root, newNode);
        this.root.isRed = false;
    }
    
    /**
     * Gets the matching value for a given key
     * @param key
     * @return value of node with given key. null if key not found
     */
    public V get(K key) {
    	if(this.root == null) return null;
   
    	Node node = this.root;
    	
    	while(node != null) {
    		if(key.compareTo(node.key) < 0) node = node.LChild; //Go left
    		else if(key.compareTo(node.key) > 0) node = node.RChild; //Go right
    		else return node.value;
    	}
    	return null;
    }
    
    /**
     * Deletes a node with the given key from the Red Black Tree
     * @param key
     * @return value of deleted node, null if key not found
     */
    @SuppressWarnings("unchecked")
	public V delete(K key) {
    	if(this.root == null) return null;
    	V root = this.root.value;
    	this.root.isRed = true; //set root red before deletion
    	Object[] theValue = new Object[1];
		//Call recursive function
    	this.root = findAndDelete(this.root, key, theValue);
    	if(this.root != null) {
    		fix(this.root); //Go back up and fix
    		this.root.isRed = false;
    		return (V) theValue[0];
    	}
    	else {
    		return root; //null
    	}
    }
    
    /**
     * Checks to see if a key is contained in the Red Black Tree
     * @param key key to search for
     * @return boolean true if key is in Red Black Tree, false otherwise
     */
    public boolean containsKey(K key) {
    	Node node = this.root;
		//Traverse down the tree
    	while(true) {
    		if(node == null) return false; //there is no node
    		if(node.key.compareTo(key) == 0) return true; //this is the node
    		if(key.compareTo(node.key) < 0) node = node.LChild; //go left
    		else node = node.RChild; //go right
    	}
    }
    
    /**
     * Checks to see if a value is contained in the Red Black Tree
     * @param value value to check for in tree
     * @return boolean true if it is contained in the Red Black Tree, false otherwise
     */
    public boolean containsValue(V value) {
        return containsValue(this.root, value);
    }
    
    /**
     * Checks to see if Red Black Tree is empty
     * @return boolean true if it is empty, false otherwise
     */
    public boolean isEmpty() {
    	return this.root == null;
    }
    
    
    /**
     * Finds the number of nodes contained in the Red Black Tree
     * @return int the size of the Red Black Tree
     */
    public int size() {
    	return this.root.size;
    }
    
    /**
     * Finds the Key for the given value in the Red Black Tree
     * @param value given value to find matching key
     * @return K key found in tree. null if key is not found
     */
    public K reverseLookup(V value) {
        return reverseLookup(root, value);
    }
    
    /**
     * Find the key less than all of the others
     * @return K lowest valued key in the Red Black Tree. null if key is not found
     */
    public K findFirstKey() {
    	if(this.root == null) return null;
    	Node node = this.root;
		//Go to the far left node
    	while(node.LChild != null) node = node.LChild;
    	return node.key;
    }
    
    /**
     * Find the greatest key in the Red Black Tree
     * @return K the highest valued key in the Red Black Tree. null if key is not found
     */
    public K findLastKey() {
    	if(this.root == null) return null;
    	Node node = this.root;
		//Go to the far right node
    	while(node.RChild != null) node = node.RChild;
    	return node.key;
    }
    
    /**
     * Finds the key of the root node of the Red Black Tree
     * @return K the key of the root node in the Red Black Tree. null if key is not found
     */
    public K getRootKey() {
    	if(this.root == null) return null;
    	return this.root.key;
    }
    
    /**
     * Finds the key immediately less than the given key
     * @param key
     * @return K key immediately less than given key. null if no predecessor is found
     */
    public K findPredecessor(K key) {
		//Start recursive function
    	Node node = findPredecessorNode(key);
    	if(node!=null) return node.key;
    	else return null;
    }
    
    /**
     * Finds the key immediately greater than the given key
     * @param key
     * @return K key immediately greater than given key. null if no successor is found
     */
    public K findSuccessor(K key) {
		//Start recursive function
    	Node node = findSuccessorNode(key);
    	if(node!=null) return node.key;
    	else return null;
    }
    
    /**
     * Finds the rank of the given key
     * @param key
     * @return int rank of the key. -1 if no node is found
     */
	public int findRank(K key) {
    	Node node = this.root;
    	int rank = 0;
    	
    	if(this.root == null) return -1;
    	
		//Traverse down the tree
    	while(node != null) {
    		if(key.compareTo(node.key) == 0) return rank + size(node.LChild);
    		else if(key.compareTo(node.key) < 0) node = node.LChild;//go left
    		else if (key.compareTo(node.key) > 0){ //go right
    			rank += 1 + size(node.LChild);
    			node = node.RChild;
    		}
    	}
    	return -1; //node not in tree
    }
    
	/**
	 * Finds the key with the given rank
	 * @param rank
	 * @return K key with the given rank. null if rank is not found
	 */
    public K select (int rank) {
    	Node node = this.root;
    	
    	if(rank < 0 || rank >= size(this.root)) return null; //rank not in range
    	
		//Traverse tree keeping track of rank
    	 while(node != null) {
    		 if(rank < size(node.LChild)) node = node.LChild; //continue left
    		 else if(rank == size(node.LChild)) return node.key; //this is the node
    		 else if(rank > size(node.LChild)) {
    			 rank -= size(node.LChild) + 1; //continue right
    			 node = node.RChild;
    		 }
    	 }
    	 return null;
    }
    
    /**
     * Counts the number of red nodes
     * @return int number of red nodes. null if tree is empty
     */
    public int countRedNodes() {
    	if(this.root == null) return 0;
    	return countRedNodes(this.root, 0);
    }
    
    /**
     * Calculates the height of the tree
     * @return int height of the tree. null if it is empty
     */
    public int calcHeight() {
    	if(this.root == null) return 0;
    	return calcHeight(this.root, 0, 0);
    }
    
    /**
     * Calculates the height of the black nodes in the tree
     * @return int height of the black nodes. null if the tree is empty
     */
    public int calcBlackHeight() {
    	if(this.root == null) return 0;
    	return calcBlackHeight(this.root, 0, 0);
    }
    
    /**
     * Finds the average depth of all nodes in the tree. Root has depth 0
     * @return double average depth of the tree
     */
    public double calcAverageDepth() {
    	if(this.root == null) return Double.NaN;
    	return calcAverageDepth(this.root, 0, 0)/size(this.root);
    }
    
    private Node findAndAdd(Node currentNode, Node newNode) {
		//Add node here?
    	if(currentNode == null) {
    		newNode.size = 1;
    		return currentNode = newNode;
    	}
    	
    	//Continue to left child?
    	if(currentNode.key.compareTo(newNode.key) > 0) {
    		currentNode.LChild = findAndAdd(currentNode.LChild, newNode);
    	}
    	//Continue to right child?
    	else if(currentNode.key.compareTo(newNode.key) < 0) {
    		currentNode.RChild = findAndAdd(currentNode.RChild, newNode);
    	}
    	//Replace node?
    	else if(currentNode.key.compareTo(newNode.key) == 0) {
    		currentNode.value = newNode.value;
    	}
    	
    	currentNode.size = 1 + size(currentNode.LChild) + size(currentNode.RChild);
    	return fix(currentNode);
    }
    
    @SuppressWarnings("unused")
	private Node findAndDelete(Node currentNode, K key, Object[] theValue) {
    	if(currentNode == null) return fix(currentNode);
    	
    	//no children?
    	if(currentNode.RChild == null && currentNode.LChild == null) {
    		if(currentNode.key.compareTo(key) == 0){
    			theValue[0] = currentNode.value;
    			assert(isRed(currentNode));
    			fix(currentNode);
    			return null; //This is it! remove from tree
    		}
    		else {
    			theValue[0] = null;
    			return fix(currentNode); //Not in Tree, save it as we recurse back up
    		}
    	}
    
    	//One left child (one right child never happens)
    	else if(currentNode.LChild != null && currentNode.RChild == null) {
    		//This is the Node
        	if(currentNode.key.compareTo(key) == 0){
        		assert(isRed(currentNode));
        		theValue[0] = currentNode.value;
        		return currentNode.LChild; //Return child to not have to worry about pointers (forget current node)
        	}
        	else{ //Continue left
        		currentNode.LChild = findAndDelete(currentNode.LChild, key, theValue);
        	}
    	}
    	
    	//if node has 2 black children
    	else if(!isRed(currentNode.LChild) && !isRed(currentNode.RChild)){
    		if(isRed(currentNode)) {
	    		flipColors(currentNode);
    		}

    		if(currentNode.key.compareTo(key) == 0) {
    			Random rand = new Random();
    			int num = rand.nextInt(2);
    			Node succ = findSuccessorNode(currentNode.key);
    			if(num == 0 || !isRed(succ)) {
    				//swap with predecessor
    				Node pred = findPredecessorNode(currentNode.key);
    				swapData(currentNode, pred);
    				currentNode.LChild = findAndDelete(currentNode.LChild, key, theValue);
    			}
    			else if(num == 1) {
    				//swap with successor
    				swapData(currentNode, succ);
    				currentNode.RChild = findAndDelete(currentNode.RChild, key, theValue);
    			}
    		}
    		else {
    			//continue right
    			if(key.compareTo(currentNode.key) > 0) {
    				currentNode.RChild = findAndDelete(currentNode.RChild, key, theValue);
        		}
    			//continue left
    			else if(key.compareTo(currentNode.key) < 0) {
    				currentNode.LChild = findAndDelete(currentNode.LChild, key, theValue);
        		}	
    		}
    	}
    	
    	//If node has left red child, and right black child
    	else if(isRed(currentNode.LChild) && !isRed(currentNode.RChild)) {
    		//need to go left
    		if(key.compareTo(currentNode.key) < 0) {
    			currentNode.LChild = findAndDelete(currentNode.LChild, key, theValue);
    		}
    		//need to go right
    		else if(key.compareTo(currentNode.key) > 0) {
    			currentNode = rotateRight(currentNode);
    			currentNode.RChild = findAndDelete(currentNode.RChild, key, theValue);
    		}	
    		//this is the node
    		else {
    			Random rand = new Random();
    			int num = rand.nextInt(2);
				Node succ = findSuccessorNode(currentNode.key);
    			if(num == 0 || !isRed(succ)) {
    				//swap with predecessor
    				Node pred = findPredecessorNode(currentNode.key);
    				swapData(currentNode, pred);
    				currentNode.LChild = findAndDelete(currentNode.LChild, key, theValue);
    			}
    			else if(num == 1) {
    				//swap with successor
    				swapData(currentNode, succ);
    				currentNode.RChild = findAndDelete(currentNode.RChild, key, theValue);
    			}
    		}
    	}
    	currentNode.size = 1 + size(currentNode.RChild) + size(currentNode.LChild);
    	return fix(currentNode);
    }
    
    private Node fix(Node node) {
    	if(node == null) return null;
    	//Two red Children
        if (isRed(node.RChild) && isRed(node.LChild)) {
        	flipColors(node);
        }
        
      //left Red Child With right Red Child
        if(isRed(node.LChild) && isRed(node.LChild.RChild)) {
        	node.LChild = rotateLeft(node.LChild);
        	node = rotateRight(node);
        }
        
      //Right Red Child With left Red Child
        if(isRed(node.RChild) && isRed(node.RChild.LChild)) {
        	node.RChild = rotateRight(node.RChild);
        	node = rotateLeft(node);
        }
        
    	//Red Right Child?
        if (isRed(node.RChild)) {
            node = rotateLeft(node);
        }
        //Two red nodes in a row?
        if (isRed(node.LChild) && isRed(node.LChild.LChild)) {
        	node = rotateRight(node);
        }
        //Two red Children
        if (isRed(node.RChild) && isRed(node.LChild)) {
        	flipColors(node);
        }
        
        if(isRed(this.root)) {
        	this.root.isRed = false;
        }
       return node;
    }
    
    private Node findSuccessorNode(K key){
    	Node node = this.root;
    	Node pred = null;
    	//find matching node
    	while(node!=null && key.compareTo(node.key) != 0) {
    		//continue right?
    		if(key.compareTo(node.key) > 0) node = node.RChild;
    		//continue left?
    		else {
    			pred = node;
    			node = node.LChild; //look left
    		}
    	}
    	//key not in tree?
    	if(node == null) return null;
    	
    	//node found, now find successor
    	//successor is in node later in tree
    	if(node.RChild != null) {
	    	node = node.RChild; //move right once
	    	while(node.LChild != null) node = node.LChild; //find leftmost child
	    	return node;
    	}
    	//successor is earlier in tree
    	else {
    		if(pred == null) return null;
    		else {
    			return pred;
    		}
    	}
    }
    
    private Node findPredecessorNode(K key) {
    	Node node = this.root;
    	Node pred = null;
    	//find matching node
    	while(node!=null && key.compareTo(node.key) != 0) {
    		//continue right?
    		if(key.compareTo(node.key) > 0) {
    			pred = node;
    			node = node.RChild;
    		}
    		//Continue left?
    		else node = node.LChild;
    	}
    	//key not in tree
    	if(node == null) return null;
    	
    	//node found, now find predecessor
    	//predecessor is after node in tree
    	if(node.LChild != null) {
	    	node = node.LChild; //move left once
	    	while(node.RChild != null) node = node.RChild; //find rightmost child
	    	return node;
    	}
    	//predecessor is before node in tree
    	else {
    		if(pred == null) return null;
    		else {
    			return pred;
    		}
    	}
    }
    	

    private Node rotateLeft(Node parent) {
        Node child = parent.RChild;
        
    	swapData(parent, child);
    	
    	parent.RChild = child.RChild;
    	
    	child.RChild = child.LChild;
    	child.LChild = parent.LChild;
    	parent.LChild = child;
    	
    	if(child.RChild != null) child.RChild.size = 1 + size(child.RChild.LChild) + size(child.RChild.RChild);
    	child.size = 1 + size(child.LChild) + size(child.RChild);
    	
    	return parent;
    }

    private Node rotateRight(Node parent) {
        Node child = parent.LChild;
        
    	swapData(parent, child);
    	
    	parent.LChild = child.LChild;
    	
    	child.LChild = child.RChild;
    	child.RChild = parent.RChild;
    	parent.RChild = child;
    	
    	if(child.LChild != null) child.LChild.size = 1 + size(child.LChild.LChild) + size(child.LChild.RChild);
    	child.size = 1 + size(child.LChild) + size(child.RChild);
    	
    	return parent;
    }
    
    private void swapData(Node x, Node y) {
    	K k = x.key;
    	V v  = x.value;
    	x.key = y.key;
    	x.value = y.value;
    	y.key = k;
    	y.value = v;
    }

    private void flipColors(Node node) {
    	if(isRed(node.RChild) == isRed(node.LChild) && isRed(node) != isRed(node.LChild)) {
	        node.isRed = !node.isRed;
	        node.LChild.isRed = !node.LChild.isRed;
	        node.RChild.isRed = !node.RChild.isRed;
    	}
    }

    private boolean containsValue(Node node, V value) {
        if (node == null) return false; //not in tree

        if (node.value.equals(value)) return true; //in tree

        //check left and right trees
        return containsValue(node.LChild, value) || containsValue(node.RChild, value);
    }

    private K reverseLookup(Node node, V value) {
        if (node == null) return null; // Not found

        if (node.value.equals(value)) return node.key; // Found a node with the given value

        K leftResult = reverseLookup(node.LChild, value);
        if (leftResult != null) return leftResult; // Found in the left subtree

        K rightResult = reverseLookup(node.RChild, value);
        if (rightResult != null) return rightResult; // Found in the right subtree

        return null; // Not found in the current subtree
    }
    
    private int countRedNodes(Node node, int size) {
        if (isRed(node)) size++; //add to size because red
        
        if (node.LChild == null) return size; // Reds from left subtree
        size = countRedNodes(node.LChild, size);

        if (node.RChild == null) return size; // Reds from right subtree
        size = countRedNodes(node.RChild, size);

        return size; // Not found in the current subtree
    }
    
    public int calcHeight(Node node, int height, int maxHeight) {
    	height += 1;
    	if(node != null && height > maxHeight) maxHeight = height;
    	
    	if (node.LChild == null) return maxHeight; // Reds from left subtree
        maxHeight = calcHeight(node.LChild, height, maxHeight);

        if (node.RChild == null) return maxHeight; // Reds from right subtree
        maxHeight = calcHeight(node.RChild, height, maxHeight);
        
        return maxHeight;
    }
    
    private int calcBlackHeight(Node node, int blackHeight, int maxBlack) {
    	//is Red and not null
    	if(node != null && !isRed(node)) blackHeight ++;
    	if(blackHeight > maxBlack) maxBlack = blackHeight;
    	
    	if (node.LChild == null) return maxBlack; // Reds from left subtree
        maxBlack = calcBlackHeight(node.LChild, blackHeight, maxBlack);

        if (node.RChild == null) return maxBlack; // Reds from right subtree
        maxBlack = calcBlackHeight(node.RChild, blackHeight, maxBlack);
        
        return maxBlack;
    }
    
	private double calcAverageDepth(Node node, int depth, double sum) {
    	if(node == null) return sum;
		sum += depth;		
    	sum = calcAverageDepth(node.LChild, depth+1, sum);
    	sum = calcAverageDepth(node.RChild, depth+1, sum);
    	
    	return sum;
    }
    
    
    private int size(Node node) {
        return (node != null) ? node.size : 0;
    }

    public String treeToString() {
        return treeToString(this.root, "", true);
    }

    private String treeToString(Node node, String prefix, boolean isTail) {
        if (node == null) return "";

        StringBuilder builder = new StringBuilder();
        builder.append(prefix);
        
        if (isTail)builder.append("└── ");
        else builder.append("├── ");
        if (node.isRed) builder.append(node.key + "(R) " + node.size);
        else builder.append(node.key + " " + node.size);
        builder.append("\n");

        String childPrefix = prefix + (isTail ? "    " : "│   ");
        String leftTree = treeToString(node.LChild, childPrefix, node.RChild == null);
        String rightTree = treeToString(node.RChild, childPrefix, true);

        // Check if the right child is null and add a black branch
        if (node.LChild == null) builder.append(childPrefix + "├── \n");
        builder.append(leftTree);
        // Check if the left child is null and add a black branch
        if (node.RChild == null) builder.append(childPrefix + "└── \n");
        builder.append(rightTree);

        return builder.toString();
    }
    
    private Boolean isRed (Node node) {
    	if(node == null) return false;
    	else return node.isRed;
    }

    private class Node {
        private K key;
        private V value;
        private boolean isRed;
        private Node RChild;
        private Node LChild;
        private int size;

        public Node(K key, V value) {
            this.key = key;
            this.value = value;
            this.isRed = true;
            this.RChild = null;
            this.LChild = null;
            this.size = 1;
        }
    }
    
    /**
     * main method
     * @param args
     */
    public static void main(String[] args) {
    	RedBlackTree<Integer, Integer> tree = new RedBlackTree<>();
        Random rand = new Random();
        int num;
        int size = 8;
        int[] nums = new int[size];
        for(int i = 0; i < size; i++) {
        	num = rand.nextInt(100);
        	nums[i] = num;
        	System.out.println("Adding: " + num);
        	tree.put(num, num);
        	System.out.println(tree.treeToString());
            System.out.println("------------------------------");
        }
   
        System.out.println("------------------------------");
        System.out.println(tree.treeToString());
        System.out.println("------------------------------");
        System.out.println("------------------------------");
        
       for(int i = 0; i < size; i++) {
        	System.out.println("Removing: " + nums[i]);
        	tree.delete(nums[i]);
        	System.out.println(tree.treeToString());
            System.out.println("------------------------------");
        }
        System.out.println("All Removed:");
        System.out.println(tree.treeToString());   

        /*System.out.println("Adding: 13");
        tree.put(13, 13);
        System.out.println("------------------------------");
        
        System.out.println("Adding: 93");
        tree.put(93, 93);
        System.out.println("------------------------------");

        System.out.println("Adding: 14");
        tree.put(14, 14);
        System.out.println("------------------------------");

        System.out.println("Adding: 93");
        tree.put(93, 93);
        System.out.println("------------------------------");

        System.out.println("Adding: 99");
        tree.put(99, 99);
        System.out.println("------------------------------");
        
        System.out.println("Adding: 72");
        tree.put(72, 72);
        System.out.println("------------------------------");

        System.out.println("Adding: 95");
        tree.put(95, 95);
        System.out.println("------------------------------");
        
        System.out.println("Adding: 28");
        tree.put(28, 28);
        System.out.println("------------------------------");

        System.out.println("Adding: 74");
        tree.put(74, 74);
        System.out.println("------------------------------");
        
        System.out.println("Adding: 8");
        tree.put(8, 8);
        System.out.println("------------------------------");      

    
        System.out.println(tree.treeToString());
        System.out.println("------------------------------");
        
        
        System.out.println("Removing: 13");
    	System.out.println(tree.delete(13));
        System.out.println("------------------------------");
        
        System.out.println("Removing: 93");
    	System.out.println(tree.delete(93));
        System.out.println("------------------------------");
        
        System.out.println("Removing: 14");
    	System.out.println(tree.delete(14));
        System.out.println("------------------------------");
        
        System.out.println("Removing: 93");
    	System.out.println(tree.delete(93));
        System.out.println("------------------------------");
        
        System.out.println("Removing: 99");
    	System.out.println(tree.delete(99));
        System.out.println("------------------------------");
        
        System.out.println("Removing: 72");
    	System.out.println(tree.delete(72));
        System.out.println("------------------------------");
        
        System.out.println("Removing: 95");
    	System.out.println(tree.delete(95));
        System.out.println("------------------------------");
        
        System.out.println("Removing: 28");
    	System.out.println(tree.delete(28));
        System.out.println("------------------------------");
        
        System.out.println("Removing: 74");
    	System.out.println(tree.delete(74));
        System.out.println("------------------------------");
        
        System.out.println("Removing: 8");
    	System.out.println(tree.delete(8));
        System.out.println("------------------------------");
        
        System.out.println(tree.treeToString());*/

    }
}
