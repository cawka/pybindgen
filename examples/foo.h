// -*- Mode: C++; c-file-style: "stroustrup"; indent-tabs-mode:nil; -*-
#ifndef   	FOO_H_
# define   	FOO_H_

#include <string>
#include <iostream>

// Yes, this code is stupid, I know; it is only meant as an example!

int print_something(const char *message);
int print_something_else(const char *message2);

int get_int_from_string(const char *from_string);
int get_int_from_float(double from_float);

// In this example PointerHolder<T> automatically implies
// caller_owns_return=True when used as ReturnValue, and
// transfer_ownership=False when used as parameter.
template <typename T>
struct PointerHolder
{
    T *thePointer;
};


class Foo
{
    std::string m_datum;
public:
    static int instance_count;

    Foo () : m_datum ("")
        { Foo::instance_count++; }
    Foo (std::string datum) : m_datum (datum)
        { Foo::instance_count++; }
    std::string get_datum () const { return m_datum; }

    Foo (Foo const & other) : m_datum (other.get_datum ())
        { Foo::instance_count++; }

    virtual ~Foo() { Foo::instance_count--; }
};

class Zoo
{
    std::string m_datum;
public:
    Zoo () : m_datum ("")
        {}
    Zoo (std::string datum) : m_datum (datum)
        {}
    virtual ~Zoo() {}
    std::string get_datum () const { return m_datum; }

    operator Foo() const {
        return Foo(m_datum);
    }
};


class ClassThatTakesFoo
{
    Foo m_foo;
public:
    ClassThatTakesFoo(Foo foo) : m_foo(foo) {}
    Foo get_foo () const { return m_foo; }
};

extern Foo g_foo;

void function_that_takes_foo(Foo foo);
Foo function_that_returns_foo();


class Bar : public Foo
{
public:
    static std::string Hooray () {
        return std::string ("Hooray!");
    }
    virtual ~Bar() {}
};

// caller owns return
Foo* get_hidden_subclass_pointer ();

class Zbr
{
    int m_refcount;
    std::string m_datum;
public:
    Zbr () : m_refcount (1), m_datum ("")
        {}
    Zbr (std::string datum) :  m_refcount (1), m_datum (datum)
        {}

    std::string get_datum () const { return m_datum; }

    Zbr (Zbr const & other) :
        m_refcount (1), m_datum (other.get_datum ())
        {}

    void Ref () {
        // std::cerr << "Ref Zbr " << this << " from " << m_refcount << std::endl;
        ++m_refcount;
    }
    void Unref () {
        // std::cerr << "Unref Zbr " << this << " from " << m_refcount << std::endl;
        if (--m_refcount == 0)
            delete this;
    }
};


class Foobar
{
public:
    static int instance_count;

    Foobar ()
        { Foobar::instance_count++; }

    virtual ~Foobar() { Foobar::instance_count--; }
};


class SomeObject
{
public:
    std::string m_prefix;

    static int instance_count;

private:
    Foo m_foo_value;
    Foo *m_foo_ptr;
    Foo *m_foo_shared_ptr;
    Zbr *m_zbr;

public:

    static std::string staticData;

    virtual ~SomeObject () {
        SomeObject::instance_count--;
        delete m_foo_ptr;
        if (m_zbr)
            m_zbr->Unref ();
    }

    SomeObject (std::string const prefix)
        : m_prefix (prefix), m_foo_ptr (0),
          m_foo_shared_ptr (0), m_zbr (0)
        {
            SomeObject::instance_count++;
        }

    SomeObject (int prefix_len)
        : m_prefix (prefix_len, 'X'), m_foo_ptr (0),
          m_foo_shared_ptr (0), m_zbr (0)
        {
            SomeObject::instance_count++;
        }

    int add_prefix (std::string& message) {
        message = m_prefix + message;
        return message.size ();
    }

    // --------  Virtual methods ----------
    virtual std::string get_prefix () const {
        return m_prefix;
    }

    std::string call_get_prefix () const {
        return get_prefix();
    }

    virtual std::string get_prefix_with_foo_value (Foo foo) const {
        return m_prefix + foo.get_datum();
    }

    virtual std::string get_prefix_with_foo_ref (const Foo &foo) const {
        return m_prefix + foo.get_datum ();
    }

    virtual std::string get_prefix_with_foo_ptr (const Foo *foo) const {
        return m_prefix + foo->get_datum ();
    }


    // pass by value, direction=in
    void set_foo_value (Foo foo) {
        m_foo_value = foo;
    }

    // pass by reference, direction=in
    void set_foo_by_ref (Foo& foo) {
        m_foo_value = foo;
    }

    // pass by reference, direction=out
    void get_foo_by_ref (Foo& foo) {
        foo = m_foo_value;
    }

    // pass by pointer, direction=in, transfers ownership
    void set_foo_ptr (Foo *foo) {
        if (m_foo_ptr)
            delete m_foo_ptr;
        m_foo_ptr = foo;
    }

    // pass by pointer, direction=in, doesn't transfer ownership
    void set_foo_shared_ptr (Foo *foo) {
        m_foo_shared_ptr = foo;
    }

    // return value
    Foo get_foo_value () {
        return m_foo_value;
    }

    // return pointer, caller doesn't own return
    Foo * get_foo_shared_ptr () {
        return m_foo_shared_ptr;
    }
    
    // return pointer, caller owns return
    Foo * get_foo_ptr () {
        Foo *foo = m_foo_ptr;
        m_foo_ptr = NULL;
        return foo;
    }

    // return reference counted object, caller owns return
    Zbr* get_zbr () {
        if (m_zbr)
        {
            m_zbr->Ref ();
            return m_zbr;
        } else
            return NULL;
    }

    // return reference counted object, caller does not own return
    Zbr* peek_zbr () { return m_zbr; }

    // pass reference counted object, transfer ownership
    void set_zbr_transfer (Zbr *zbr) {
        if (m_zbr)
            m_zbr->Unref ();
        m_zbr = zbr;
    }

    // pass reference counted object, does not transfer ownership
    void set_zbr_shared (Zbr *zbr) {
        if (m_zbr)
            m_zbr->Unref ();
        zbr->Ref ();
        m_zbr = zbr;
    }


    // return reference counted object, caller does not own return
    PointerHolder<Zbr> get_zbr_pholder () {
        PointerHolder<Zbr> foo = { m_zbr };
        m_zbr->Ref ();
        return foo;
    }

    // pass reference counted object, transfer ownership
    void set_zbr_pholder (PointerHolder<Zbr> zbr) {
        if (m_zbr)
            m_zbr->Unref ();
        m_zbr = zbr.thePointer;
        m_zbr->Ref ();
    }

    int get_int (const char *from_string);
    int get_int (double from_float);

    // custodian/ward tests
    Foobar* get_foobar_with_self_as_custodian () {
        return new Foobar;
    }
    Foobar* get_foobar_with_other_as_custodian (const SomeObject *other) {
        other++;
        return new Foobar;
    }
    void set_foobar_with_self_as_custodian (Foobar *foobar) {
        foobar++;
    }
};


// A function that will appear as a method of SomeObject
// obj: transfer_ownership=false
std::string some_object_get_something_prefixed(const SomeObject *obj, const std::string something);

std::string some_object_val_get_something_prefixed(SomeObject obj, const std::string something);
std::string some_object_ref_get_something_prefixed(const SomeObject &obj, const std::string something);


// Transfer ownership of 'obj' to the library
void store_some_object(SomeObject *obj);

// Invokes the virtual method in the stored SomeObject
std::string invoke_some_object_get_prefix();

// Transfer ownership of 'obj' away from the library
SomeObject* take_some_object();

// Deletes the contained object, if any
void delete_some_object();


namespace xpto
{
    std::string some_function();

    class SomeClass
    {
    public:
        SomeClass() {}
    };

    enum FooType {
        FOO_TYPE_AAA,
        FOO_TYPE_BBB,
        FOO_TYPE_CCC,
    };

    FooType get_foo_type ();
    void set_foo_type (FooType type);
}

Foobar* get_foobar_with_other_as_custodian(const SomeObject *other);

Foobar* create_new_foobar();
void set_foobar_with_other_as_custodian(Foobar *foobar, const SomeObject *other);
SomeObject * set_foobar_with_return_as_custodian(Foobar *foobar);

class SingletonClass
{
private:
    static SingletonClass *m_instance;

    SingletonClass () {}
    ~SingletonClass () {}

public:
    static SingletonClass *GetInstance ()
        {
            if (not m_instance)
                m_instance = new SingletonClass;
            return m_instance;
        }
};


#endif 	    /* !FOO_H_ */
